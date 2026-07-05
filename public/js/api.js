console.log("API JS v13000 loaded");

window.API = {
  async details(symbol, range = "1D") {
    const cleanSymbol = String(symbol || "").trim().toUpperCase();
    const cleanRange = String(range || "1D").trim().toUpperCase();

    if (!cleanSymbol) {
      throw new Error("Symbol is empty.");
    }

    const response = await fetch(
      `/api/details?symbol=${encodeURIComponent(cleanSymbol)}&range=${encodeURIComponent(cleanRange)}`
    );

    const json = await response.json();

    if (!response.ok || !json.ok) {
      throw new Error(json.error || "Data could not be loaded.");
    }

    return json.data;
  },

  async quote(symbol) {
    const data = await this.details(symbol, "1D");
    return data.quote;
  },

  async history(symbol, range = "1D") {
    const data = await this.details(symbol, range);
    return data.history;
  }
};
