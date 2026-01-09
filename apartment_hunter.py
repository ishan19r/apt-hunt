#!/usr/bin/env python3
"""
Automated Apartment Hunter for Ishan
- Budget: $2,600-$3,200/month
- Location: Manhattan (East Harlem, UES, Yorkville preferred)
- Requirements: 1BR, no broker fee preferred
"""

CRITERIA = {
    "min_rent": 2400,
    "max_rent": 3200,
    "bedrooms": 1,
    "neighborhoods": ["east-harlem", "yorkville", "upper-east-side", "harlem", "washington-heights", "inwood"],
    "no_fee_preferred": True,
    "income": 110000,
}

def check_affordability(rent):
    return CRITERIA["income"] >= rent * 40

def generate_inquiry(address):
    return f"""Hi,

I'm interested in the 1-bedroom at {address}. A few questions:

1. Is the unit still available for immediate move-in?
2. Are there any additional fees beyond rent?
3. What are the income/credit requirements for approval?
4. Is there any flexibility on the lease terms?

I'm available weekdays after 5:30pm or weekends anytime.

Thanks!
Ishan"""

def calculate_budget(rent):
    take_home = 5250
    after_rent = take_home - rent
    return {"rent": rent, "utilities": 150, "groceries": 400, "transport": 132, "dining_out": min(500, after_rent - 682), "savings": max(0, after_rent - 1182)}

def main():
    print("🏠 ISHAN'S APARTMENT HUNTER")
    print(f"Budget: ${CRITERIA['min_rent']:,} - ${CRITERIA['max_rent']:,}")
    print(f"Max rent (40x rule): ${CRITERIA['income']//40:,}/mo")
    print("\nBUDGET SCENARIOS:")
    for rent in [2600, 2800, 3000, 3200]:
        b = calculate_budget(rent)
        status = "✅ PASS" if check_affordability(rent) else "❌ FAIL"
        print(f"${rent}: {status} | Dining: ${b['dining_out']} | Savings: ${b['savings']}")

if __name__ == "__main__":
    main()
