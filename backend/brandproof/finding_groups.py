"""Group snapshot findings by the same authoritative rule, without merging spans."""


def finding_groups(findings):
    grouped = {}
    for item in findings:
        evidence = item.get("evidence")
        # Uncited findings stay separate; never imply they share an authority.
        key = (
            (item["category"], evidence["source_id"], evidence["source_version"])
            if evidence
            else (item["category"], None, item["id"])
        )
        if key not in grouped:
            grouped[key] = {
                "category": item["category"],
                "source_id": evidence["source_id"] if evidence else None,
                "source_version": evidence["source_version"] if evidence else None,
                "finding_ids": [],
                "assets": [],
            }
        group = grouped[key]
        group["finding_ids"].append(item["id"])
        asset = item["location"]["asset"]
        if asset not in group["assets"]:
            group["assets"].append(asset)
    return list(grouped.values())
