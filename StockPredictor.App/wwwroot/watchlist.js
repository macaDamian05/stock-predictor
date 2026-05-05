window.stockPredictorWatchlist = {
    get: function () {
        try {
            const raw = window.localStorage.getItem("stockpredictor-watchlist-v1");
            const value = raw ? JSON.parse(raw) : [];
            return Array.isArray(value) ? value : [];
        } catch {
            return [];
        }
    },
    set: function (tickers) {
        try {
            const normalized = Array.isArray(tickers) ? tickers : [];
            window.localStorage.setItem("stockpredictor-watchlist-v1", JSON.stringify(normalized));
        } catch {
            // Ignore storage errors and keep the current in-memory state.
        }
    }
};
