from legalpulse_nlp import RuleBasedNLIBackend

# p4 pair: unrelated clauses that share only time words
PAY = "Within 15 days of receiving an invoice, Licensee shall pay the annual Licence Fee."
DEL = "Licensor shall delete Licensee data within 30 days of termination."


def _label(a, b):
    p = RuleBasedNLIBackend().predict([(a, b)])[0]
    return max(p, key=p.get)


def test_unrelated_clauses_sharing_only_time_words_not_contradiction():
    assert _label(PAY, DEL) != "contradiction"
    assert _label(DEL, PAY) != "contradiction"


def test_same_topic_different_figure_still_contradiction():
    a = "Buyer shall pay each invoice within 30 days."
    b = "Buyer shall pay each invoice within 45 days."
    assert _label(a, b) == "contradiction"


def test_same_topic_forbid_vs_allow_still_contradiction():
    a = "Tenant may sublet the premises to a third party."
    b = "Tenant shall not sublet the premises to a third party."
    assert _label(a, b) == "contradiction"
