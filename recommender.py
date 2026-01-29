import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

def load_rules(csv_path):
    df = pd.read_csv(csv_path, header=None)

    transactions = df.apply(
        lambda row: [item.strip().lower() for item in row.dropna()],
        axis=1
    ).tolist()

    encoder = TransactionEncoder()
    encoded = encoder.fit(transactions).transform(transactions)
    encoded_df = pd.DataFrame(encoded, columns=encoder.columns_)

    freq_items = apriori(encoded_df, min_support=0.01, use_colnames=True)
    rules = association_rules(freq_items, metric="confidence", min_threshold=0.2)

    return rules

def get_recommendations(product, rules, limit=5):
    product = product.lower()
    recs = set()

    matched = rules[
        rules['antecedents'].apply(
            lambda x: product in [i.lower() for i in x]
        )
    ]

    for items in matched['consequents']:
        for item in items:
            if item.lower() != product:
                recs.add(item)

    return list(recs)[:limit]
