# utils/ttak_api.py
import requests
from PyQt6.QtGui import QAction
def fetch_data_from_ttak_api(search_term):
    api_url = f"https://newapi.ttac.ir/irfdamobile/v1/getnfisearch?Term={search_term}&PageNumber=1&PageSize=10&IP="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Accept": "*/*", "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,fa;q=0.7,fr;q=0.6", "Connection": "keep-alive",
        "Host": "newapi.ttac.ir", "Origin": "https://mobile.ttac.ir", "Referer": "https://mobile.ttac.ir/",
        "Sec-Ch-Ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"', "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"', "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site", "x-ssp-api-key": "dbd69ca2-7096-4e19-ad26-74a3a33f3516" 
    }
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        drugs = []
        if "data" in data and "drugLicenses" in data["data"] and data["data"]["drugLicenses"]:
            for drug in data["data"]["drugLicenses"]:
                quantity_per_box_str = drug.get("unitOfUsePackaging", "0 in 0")
                try: quantity_per_box = int(quantity_per_box_str.split(" in ")[0].split()[0])
                except (ValueError, IndexError): quantity_per_box = 0

                price_per_unit = int(drug.get("packageConsumerPrice", 0)) // max(1, quantity_per_box) if quantity_per_box > 0 else int(drug.get("packageConsumerPrice", 0))
                dosage = drug.get("strength", "نامشخص")
                if dosage == "نامشخص" and drug.get("drugGenericFaName"):
                    dosage_parts = drug.get("drugGenericFaName", "").split()
                    dosage = next((part for part in dosage_parts if any(c.isdigit() for c in part)), "نامشخص")
                form = drug.get("dosageFormFa", "نامشخص")
                if form == "نامشخص" and drug.get("drugGenericFaName"):
                    form_parts = drug.get("drugGenericFaName", "").split()
                    non_chemical_parts = [p for p in form_parts if p.lower() not in ["hydrochloride", "chloride", "sodium", "potassium", "calcium", "maleate", "succinate", "phosphate", "acetate", "sulfate", "هیدروکلراید", "کلراید", "سدیم"]]
                    form = next((p for p in non_chemical_parts if not any(c.isdigit() for c in p) and len(p) > 1), "نامشخص")

                en_brand_name = drug.get("enBrandName", "Unknown")
                generic_name = drug.get("genericName", en_brand_name) 
                if generic_name == en_brand_name or not generic_name:
                    fa_generic_parts = drug.get("drugGenericFaName", "").split()
                    if fa_generic_parts:
                        potential_generic = [p for p in fa_generic_parts if not any(c.isdigit() for c in p) and p not in [form, dosage] and len(p) > 2]
                        generic_name = potential_generic[0] if potential_generic else drug.get("genericName", en_brand_name)

                generic_code = str(drug.get("drugGenericCode", "نامشخص"))
                drugs.append({
                    "generic_name": generic_name, "en_brand_name": en_brand_name,
                    "generic_code": generic_code, "form": form, "dosage": dosage,
                    "price_per_unit": price_per_unit
                })
        return drugs
    except Exception as e:
        print(f"ttak api err on {search_term}: {str(e)}")
        return []