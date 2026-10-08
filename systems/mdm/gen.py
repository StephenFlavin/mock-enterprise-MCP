"""MDM master data: vendor records with duplicates, bank details, audit trail, and data ownership."""
import hashlib
import random
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    fake = g.fake

    # Get all suppliers from master
    suppliers = g.master("suppliers")
    employees = g.master("employees")
    # Bank-detail edits are made by finance staff, not warehouse operatives.
    finance = [e for e in employees if e["role"] in ("Financial Analyst", "Management Accountant")]

    vendor_master = []
    vendor_bank_details = []
    vendor_bank_changes = []
    data_owners = []

    # Create vendor records: one per supplier, plus some duplicates with typos/variations
    vendor_counter = 1
    first_bank = {}  # vendor_id -> its first bank detail row
    vendor_map = {}  # Maps supplier_id to vendor_id for consistent references
    bank_detail_counter = 1
    change_counter = 1

    for sup in suppliers[:250]:  # Create vendors for first 250 suppliers
        base_vendor_id = f"VEN-{vendor_counter:06d}"
        vendor_map[sup["supplier_id"]] = base_vendor_id
        vendor_counter += 1

        # Main vendor record
        vendor_master.append({
            "vendor_id": base_vendor_id,
            "name": sup["name"],
            "address": f"{fake.street_address()}, {fake.city()}",
            "tax_id": f"TAX-{r.randint(100000, 999999)}",
            "country": sup["country"],
            "status": "active",
            "merged_into": "",
            "bank_account_hash": "",
            "merged_at": None,
            "updated_at": g.as_of
        })

        # Create 1-2 bank detail records per vendor
        bank_count = r.choice([1, 2])
        for _ in range(bank_count):
            account_hash = hashlib.md5(f"{base_vendor_id}_{bank_detail_counter}".encode()).hexdigest()[:16]
            bank_detail_id = f"BNK-{bank_detail_counter:06d}"
            bank_detail_counter += 1

            vendor_master[-1]["bank_account_hash"] = account_hash  # Link to vendor

            vendor_bank_details.append({
                "bank_detail_id": bank_detail_id,
                "vendor_id": base_vendor_id,
                "account_number": f"****{r.randint(1000, 9999)}",
                "sort_code": f"{r.randint(10, 99)}-{r.randint(10, 99)}-{r.randint(10, 99)}",
                "iban": f"GB{r.randint(10, 99)} {fake.bothify(text='???? ???? ???? ???? ???? ??').upper()}",
                "bank_name": r.choice(["HSBC", "Barclays", "Lloyds", "NatWest", "RBS", "Santander"]),
                "account_holder": sup["name"],
                "currency": sup["currency"] or "GBP",
                "status": "active",
                "created_at": g.as_of - timedelta(days=r.randint(30, 365)),
                "archived_at": None
            })

            first_bank.setdefault(base_vendor_id, vendor_bank_details[-1])

            # Add a change record for this bank detail
            vendor_bank_changes.append({
                "change_id": f"CHG-{change_counter:06d}",
                "vendor_id": base_vendor_id,
                "changed_at": vendor_bank_details[-1]["created_at"],
                "changed_by": r.choice(finance)["employee_id"],
                "field_changed": "bank_details",
                "old_value": "",
                "new_value": bank_detail_id,
                "change_type": "added"
            })
            change_counter += 1

    # Create duplicate vendor records with typos/variations
    duplicates_created = 0
    for i in range(0, 60, 4):  # a modest number of duplicates (15)
        orig = vendor_master[i]
        if orig["status"] != "active":
            continue
        ob = first_bank[orig["vendor_id"]]

        # Create a duplicate with name variation
        dup_name = orig["name"]
        # Add subtle variations
        variations = [
            dup_name + " Inc",
            dup_name.replace("Ltd", "Limited"),
            dup_name.replace("&", "and"),
            dup_name.upper(),
            " ".join(dup_name.split()[:-1]) if len(dup_name.split()) > 1 else dup_name,  # Drop last word
        ]
        dup_name = r.choice(variations)

        dup_vendor_id = f"VEN-{vendor_counter:06d}"
        vendor_counter += 1
        duplicates_created += 1

        # Mark as duplicate to flag in validation
        vendor_master.append({
            "vendor_id": dup_vendor_id,
            "name": dup_name,
            "address": orig["address"],  # Same address as original
            "tax_id": orig["tax_id"],  # Same tax ID as original
            "country": orig["country"],
            "status": "duplicate",
            "merged_into": "",
            "bank_account_hash": orig["bank_account_hash"],  # Share bank account hash
            "merged_at": None,
            "updated_at": g.as_of
        })

        # Add bank detail for duplicate pointing to same bank account
        bank_detail_id = f"BNK-{bank_detail_counter:06d}"
        bank_detail_counter += 1
        created = g.as_of - timedelta(days=r.randint(30, 300))  # old enough not to crowd recent-change questions

        vendor_bank_details.append({
            "bank_detail_id": bank_detail_id,
            "vendor_id": dup_vendor_id,
            "account_number": ob["account_number"],  # Same account as original
            "sort_code": ob["sort_code"],
            "iban": ob["iban"],
            "bank_name": ob["bank_name"],
            "account_holder": dup_name,
            "currency": ob["currency"],
            "status": "active",
            "created_at": created,
            "archived_at": None
        })
        vendor_bank_changes.append({
            "change_id": f"CHG-{change_counter:06d}",
            "vendor_id": dup_vendor_id,
            "changed_at": created,
            "changed_by": r.choice(finance)["employee_id"],
            "field_changed": "bank_details",
            "old_value": "",
            "new_value": bank_detail_id,
            "change_type": "added"
        })
        change_counter += 1

    # Background: a few routine bank-detail edits, all well before the recent window
    for vid, bd in list(first_bank.items())[40:52]:
        vendor_bank_changes.append({
            "change_id": f"CHG-{change_counter:06d}",
            "vendor_id": vid,
            "changed_at": g.as_of - timedelta(days=r.randint(70, 240)),
            "changed_by": r.choice(finance)["employee_id"],
            "field_changed": "bank_name",
            "old_value": r.choice(["HSBC", "Barclays", "Lloyds", "NatWest"]),
            "new_value": bd["bank_name"],
            "change_type": "modified"
        })
        change_counter += 1

    # Create data ownership records for different domains
    domains = [
        {"name": "Product Master Data", "domain": "products", "slo": 99.5},
        {"name": "Vendor Master Data", "domain": "vendors", "slo": 98.0},
        {"name": "Site Master Data", "domain": "sites", "slo": 99.0},
        {"name": "Customer Master Data", "domain": "customers", "slo": 97.0},
        {"name": "Order Data", "domain": "orders", "slo": 95.0},
        {"name": "Supplier Performance", "domain": "suppliers", "slo": 96.0},
    ]

    for i, domain in enumerate(domains):
        owner = r.choice(employees)
        steward = r.choice(employees)
        data_owners.append({
            "dataset_id": f"DST-{i+1:03d}",
            "name": domain["name"],
            "domain": domain["domain"],
            "owner_id": owner["employee_id"],
            "steward_id": steward["employee_id"],
            "slo_accuracy_pct": domain["slo"],
            "last_audit_date": g.as_of - timedelta(days=r.randint(10, 90))
        })

    return {
        "vendor_master": vendor_master,
        "vendor_bank_details": vendor_bank_details,
        "vendor_bank_changes": vendor_bank_changes,
        "data_owners": data_owners
    }
