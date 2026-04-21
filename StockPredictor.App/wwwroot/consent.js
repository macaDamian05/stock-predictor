window.stockPredictorConsent = {
    getAccepted: function () {
        try {
            return window.localStorage.getItem("stockpredictor-risk-consent-v1") === "accepted";
        } catch {
            return false;
        }
    },
    accept: function () {
        try {
            window.localStorage.setItem("stockpredictor-risk-consent-v1", "accepted");
        } catch {
            // Ignore storage errors and keep the current in-memory accepted state.
        }
    }
};
