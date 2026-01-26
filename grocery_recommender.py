import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules


# def load_transactions(csv_path):
#     """
#     Load grocery transactions from CSV file.
#     Each row represents one transaction.
#     Empty cells are ignored.
#     """
#     df = pd.read_csv(csv_path, header=None) # df = pd.read_csv(csv_path)
#     transactions = df.apply(lambda row: row.dropna().tolist(), axis=1).tolist()
#     return transactions
def load_transactions(csv_path):
    """
    Load grocery transactions from CSV file.
    Each row represents one transaction.
    File has NO header row.
    """
    df = pd.read_csv(csv_path, header=None)
    transactions = df.apply(lambda row: row.dropna().tolist(), axis=1).tolist()
   
    transactions = [
    [item.strip().lower() for item in row.dropna().tolist()]
    for _, row in df.iterrows()
    ]
    return transactions




def encode_transactions(transactions):
    """
    Convert transactions into one-hot encoded dataframe
    required by Apriori algorithm.
    """
    encoder = TransactionEncoder()
    encoded_array = encoder.fit(transactions).transform(transactions)
    encoded_df = pd.DataFrame(encoded_array, columns=encoder.columns_)
    return encoded_df


# def generate_rules(encoded_df, min_support=0.05, min_confidence=0.05):
# def generate_rules(encoded_df, min_support=0.01, min_confidence=0.2):

#     """
#     Generate frequent itemsets and association rules
#     """
#     frequent_items = apriori(
#         encoded_df,
#         min_support=min_support,
#         use_colnames=True
#     )

#     rules = association_rules(
#         frequent_items,
#         metric="confidence",
#         min_threshold=min_confidence
#     )

#     return rules

def generate_rules(encoded_df, min_support=0.01, min_confidence=0.2):
    frequent_items = apriori(
        encoded_df,
        min_support=min_support,
        use_colnames=True
    )

    rules = association_rules(
        frequent_items,
        metric="confidence",
        min_threshold=min_confidence
    )

    return rules



def recommend_product(rules, product):
    """
    Recommend products based on association rules
    """
    product = product.strip().lower()
    print("\nTop rules preview:")
    print(rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].head(5))


    filtered_rules = rules[
        rules['antecedents'].apply(
            lambda x: product in [item.lower() for item in x]
        )
    ]

    if filtered_rules.empty:
        print("\nNo recommendation found.")
        return

    print(f"\nSince you bought '{product}', you might also like:")
    recommendations = set()

    for consequents in filtered_rules['consequents']:
        for item in consequents:
            recommendations.add(item)

    for item in recommendations:
        print(f" - {item}")


def main():
    print("Grocery Store Recommendation System")
    print("----------------------------------")

    csv_path = "groceries.csv"  # Must be in same folder
    try:
        transactions = load_transactions(csv_path)
    except FileNotFoundError:
        print("ERROR: groceries.csv not found in project folder.")
        return

    encoded_df = encode_transactions(transactions)
    rules = generate_rules(encoded_df)
    print("\nTotal rules generated:", len(rules))


    while True:
        product = input("\nEnter a product name (or type 'exit' to quit): ")
        if product.lower() == "exit":
            print("Exiting system.")
            break

        recommend_product(rules, product)


if __name__ == "__main__":
    main()
