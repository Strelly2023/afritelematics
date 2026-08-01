# Security-version model

Each identity now has a durable integer security version. Issued access tokens capture it; validation compares it to current durable state. A local test proves an increment rejects the old token while a newly issued token carries the current version.
