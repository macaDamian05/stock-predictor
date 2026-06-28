window.stockPredictorProfile = (() => {
    const profileKey = "stockpredictor-local-profile-v1";

    function getRaw() {
        try {
            return window.localStorage.getItem(profileKey);
        } catch {
            return null;
        }
    }

    function setRaw(value) {
        try {
            window.localStorage.setItem(profileKey, value || "");
            return true;
        } catch {
            return false;
        }
    }

    function remove() {
        try {
            window.localStorage.removeItem(profileKey);
            return true;
        } catch {
            return false;
        }
    }

    async function copyText(value) {
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(value || "");
                return true;
            }
        } catch {
            return false;
        }

        return false;
    }

    return {
        getRaw,
        setRaw,
        remove,
        copyText
    };
})();
