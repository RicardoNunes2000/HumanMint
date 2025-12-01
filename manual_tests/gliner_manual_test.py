import sys

sys.path.insert(0, "src")
from humanmint import mint

SAMPLE_TEXT = """
John A. Miller
Deputy Director of Public Works
City of Springfield, Missouri
305 E McDaniel St, Springfield, MO 65806
Phone: (417) 864-1234
Email: jmiller@springfieldmo.gov
"""

SAMPLE_TEXT_2 = """
STATE  O F  M I N N E S O T A   
D E P T O F  H U M A N   S E R V I C E S  
Chi l d   Wel f a re  D iv is i o n  

OF F I C E    C O N T A C T

Ka t h e r i n e  J.  Ba u m berg er
P r o g ra m   S u p ervi so r
Ema i l :   k j bau m b erg er @ s t a t e . m n . u s
Ph :  651 - 4 3 1 - 2 2 0 1
321  no r th  Robert  S t,  
St   Pau l ,  MN   55101

"""

# Toggle this flag to exercise GLiNER extraction when installed
USE_GLINER = True


def main():
    try:
        results = mint(
            texts=[SAMPLE_TEXT, SAMPLE_TEXT_2],
            use_gliner=USE_GLINER,
            gliner_use_gpu=True,
            split_multi=True,
        )
    except Exception as e:
        print("[ERROR]", e)
        return

    if isinstance(results, list):
        print(f"Got {len(results)} results from split_multi + gliner")
        for idx, res in enumerate(results, 1):
            print(f"--- Result {idx} ---")
            print(res)
    else:
        print(results)
        print("\nName:", results.name)
        print("Email:", results.email)
        print("Phone:", results.phone)
        print("Department:", results.department)
        print("Title:", results.title)
        print("Address:", results.address)
        print("Organization:", results.organization)


if __name__ == "__main__":
    main()
