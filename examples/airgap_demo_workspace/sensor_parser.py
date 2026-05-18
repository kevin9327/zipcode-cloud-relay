def parse_reading(row):
    """Parse one CSV row: site_id,turbidity,chlorine."""
    site_id, turbidity, chlorine = row.strip().split(",")
    turbidity_value = float(turbidity)
    chlorine_value = float(chlorine)

    # Bug for the demo: negative turbidity is physically invalid but accepted.
    if chlorine_value < 0:
        raise ValueError("chlorine cannot be negative")

    return {
        "site_id": site_id,
        "turbidity": turbidity_value,
        "chlorine": chlorine_value,
    }


if __name__ == "__main__":
    print(parse_reading("well-17,-3.2,0.4"))
