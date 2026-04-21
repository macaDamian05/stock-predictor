using System.Text.Json.Serialization;

namespace StockPredictor.App.Models;

public sealed class DashboardPayload
{
    [JsonPropertyName("ui_contract_version")]
    public string UiContractVersion { get; init; } = string.Empty;

    [JsonPropertyName("generated_at")]
    public DateTime GeneratedAt { get; init; }

    [JsonPropertyName("source_runs")]
    public DashboardSourceRuns SourceRuns { get; init; } = new();

    [JsonPropertyName("summary_cards")]
    public DashboardSummaryCards SummaryCards { get; init; } = new();

    [JsonPropertyName("featured_tickers")]
    public List<FeaturedTicker> FeaturedTickers { get; init; } = [];

    [JsonPropertyName("company_ranking")]
    public List<CompanyRankingEntry> CompanyRanking { get; init; } = [];

    [JsonPropertyName("basket_summaries")]
    public List<BasketSummary> BasketSummaries { get; init; } = [];

    [JsonPropertyName("notes")]
    public List<string> Notes { get; init; } = [];
}

public sealed class DashboardSourceRuns
{
    [JsonPropertyName("thesis_run")]
    public string ThesisRun { get; init; } = string.Empty;

    [JsonPropertyName("starter_suite")]
    public string StarterSuite { get; init; } = string.Empty;

    [JsonPropertyName("core_profile_comparison")]
    public string CoreProfileComparison { get; init; } = string.Empty;

    [JsonPropertyName("diversified_profile_comparison")]
    public string DiversifiedProfileComparison { get; init; } = string.Empty;
}

public sealed class DashboardSummaryCards
{
    [JsonPropertyName("starter_best_experiment")]
    public StarterBestExperimentSummary StarterBestExperiment { get; init; } = new();

    [JsonPropertyName("starter_tickers_beating_baseline")]
    public List<string> StarterTickersBeatingBaseline { get; init; } = [];

    [JsonPropertyName("best_core_profile")]
    public ProfileSummaryCard BestCoreProfile { get; init; } = new();

    [JsonPropertyName("best_diversified_profile")]
    public ProfileSummaryCard BestDiversifiedProfile { get; init; } = new();
}

public sealed class StarterBestExperimentSummary
{
    [JsonPropertyName("experiment_id")]
    public string ExperimentId { get; init; } = string.Empty;

    [JsonPropertyName("feature_profile")]
    public string FeatureProfile { get; init; } = string.Empty;

    [JsonPropertyName("lags")]
    public int Lags { get; init; }

    [JsonPropertyName("ticker_count")]
    public int TickerCount { get; init; }

    [JsonPropertyName("successful_tickers")]
    public int SuccessfulTickers { get; init; }

    [JsonPropertyName("failed_tickers")]
    public int FailedTickers { get; init; }

    [JsonPropertyName("mean_walk_forward_baseline_rmse")]
    public double MeanWalkForwardBaselineRmse { get; init; }

    [JsonPropertyName("mean_best_learned_rmse")]
    public double MeanBestLearnedRmse { get; init; }

    [JsonPropertyName("mean_best_learned_directional_accuracy")]
    public double MeanBestLearnedDirectionalAccuracy { get; init; }

    [JsonPropertyName("mean_best_learned_minus_baseline_rmse")]
    public double MeanBestLearnedMinusBaselineRmse { get; init; }

    [JsonPropertyName("dominant_best_model")]
    public string DominantBestModel { get; init; } = string.Empty;

    [JsonPropertyName("ridge_wins")]
    public int RidgeWins { get; init; }

    [JsonPropertyName("decision_tree_wins")]
    public int DecisionTreeWins { get; init; }

    [JsonPropertyName("random_forest_wins")]
    public int RandomForestWins { get; init; }

    [JsonPropertyName("dominant_best_model_label")]
    public string DominantBestModelLabel { get; init; } = string.Empty;
}

public sealed class ProfileSummaryCard
{
    [JsonPropertyName("feature_profile")]
    public string FeatureProfile { get; init; } = string.Empty;

    [JsonPropertyName("ticker_count")]
    public int TickerCount { get; init; }

    [JsonPropertyName("mean_walk_forward_baseline_rmse")]
    public double MeanWalkForwardBaselineRmse { get; init; }

    [JsonPropertyName("mean_best_learned_rmse")]
    public double MeanBestLearnedRmse { get; init; }

    [JsonPropertyName("mean_best_learned_directional_accuracy")]
    public double MeanBestLearnedDirectionalAccuracy { get; init; }

    [JsonPropertyName("mean_best_learned_minus_baseline_rmse")]
    public double MeanBestLearnedMinusBaselineRmse { get; init; }

    [JsonPropertyName("dominant_best_model")]
    public string DominantBestModel { get; init; } = string.Empty;

    [JsonPropertyName("feature_profile_label")]
    public string FeatureProfileLabel { get; init; } = string.Empty;

    [JsonPropertyName("dominant_best_model_label")]
    public string DominantBestModelLabel { get; init; } = string.Empty;
}

public sealed class FeaturedTicker
{
    [JsonPropertyName("ticker")]
    public string Ticker { get; init; } = string.Empty;

    [JsonPropertyName("forecast_model")]
    public string ForecastModel { get; init; } = string.Empty;

    [JsonPropertyName("forecast_model_label")]
    public string ForecastModelLabel { get; init; } = string.Empty;

    [JsonPropertyName("last_close_date")]
    public DateOnly LastCloseDate { get; init; }

    [JsonPropertyName("last_close")]
    public double LastClose { get; init; }

    [JsonPropertyName("next_forecast_date")]
    public DateOnly NextForecastDate { get; init; }

    [JsonPropertyName("next_predicted_close")]
    public double NextPredictedClose { get; init; }

    [JsonPropertyName("next_predicted_change_pct")]
    public double NextPredictedChangePct { get; init; }

    [JsonPropertyName("forecast_end_date")]
    public DateOnly ForecastEndDate { get; init; }

    [JsonPropertyName("forecast_end_close")]
    public double ForecastEndClose { get; init; }

    [JsonPropertyName("forecast_horizon_change_pct")]
    public double ForecastHorizonChangePct { get; init; }

    [JsonPropertyName("forecast_days")]
    public int ForecastDays { get; init; }

    [JsonPropertyName("average_recent_rsi")]
    public double AverageRecentRsi { get; init; }

    [JsonPropertyName("average_forecast_slope")]
    public double AverageForecastSlope { get; init; }

    [JsonPropertyName("average_forecast_distance_to_last_close")]
    public double AverageForecastDistanceToLastClose { get; init; }

    [JsonPropertyName("average_forecast_distance_pct_to_last_close")]
    public double AverageForecastDistancePctToLastClose { get; init; }

    [JsonPropertyName("feature_profile")]
    public string FeatureProfile { get; init; } = string.Empty;

    [JsonPropertyName("feature_profile_label")]
    public string FeatureProfileLabel { get; init; } = string.Empty;

    [JsonPropertyName("holdout_best_model")]
    public string HoldoutBestModel { get; init; } = string.Empty;

    [JsonPropertyName("walk_forward_best_model")]
    public string WalkForwardBestModel { get; init; } = string.Empty;

    [JsonPropertyName("walk_forward_best_rmse")]
    public double WalkForwardBestRmse { get; init; }

    [JsonPropertyName("walk_forward_baseline_rmse")]
    public double WalkForwardBaselineRmse { get; init; }

    [JsonPropertyName("walk_forward_best_directional_accuracy")]
    public double WalkForwardBestDirectionalAccuracy { get; init; }

    [JsonPropertyName("beats_baseline_rmse")]
    public bool BeatsBaselineRmse { get; init; }

    [JsonPropertyName("data_start")]
    public DateOnly DataStart { get; init; }

    [JsonPropertyName("data_end")]
    public DateOnly DataEnd { get; init; }

    [JsonPropertyName("forecast_path")]
    public List<ForecastPoint> ForecastPath { get; init; } = [];
}

public sealed class ForecastPoint
{
    [JsonPropertyName("date")]
    public DateOnly Date { get; init; }

    [JsonPropertyName("predicted_return")]
    public double PredictedReturn { get; init; }

    [JsonPropertyName("predicted_close")]
    public double PredictedClose { get; init; }
}

public sealed class CompanyRankingEntry
{
    [JsonPropertyName("rank")]
    public int Rank { get; init; }

    [JsonPropertyName("ticker")]
    public string Ticker { get; init; } = string.Empty;

    [JsonPropertyName("ranking_score")]
    public double RankingScore { get; init; }

    [JsonPropertyName("forecast_model")]
    public string ForecastModel { get; init; } = string.Empty;

    [JsonPropertyName("forecast_model_label")]
    public string ForecastModelLabel { get; init; } = string.Empty;

    [JsonPropertyName("feature_profile")]
    public string FeatureProfile { get; init; } = string.Empty;

    [JsonPropertyName("feature_profile_label")]
    public string FeatureProfileLabel { get; init; } = string.Empty;

    [JsonPropertyName("last_close")]
    public double LastClose { get; init; }

    [JsonPropertyName("next_predicted_change_pct")]
    public double NextPredictedChangePct { get; init; }

    [JsonPropertyName("forecast_horizon_change_pct")]
    public double ForecastHorizonChangePct { get; init; }

    [JsonPropertyName("average_forecast_distance_to_last_close")]
    public double AverageForecastDistanceToLastClose { get; init; }

    [JsonPropertyName("average_forecast_distance_pct_to_last_close")]
    public double AverageForecastDistancePctToLastClose { get; init; }

    [JsonPropertyName("walk_forward_best_directional_accuracy")]
    public double WalkForwardBestDirectionalAccuracy { get; init; }

    [JsonPropertyName("walk_forward_best_rmse")]
    public double WalkForwardBestRmse { get; init; }

    [JsonPropertyName("walk_forward_baseline_rmse")]
    public double WalkForwardBaselineRmse { get; init; }

    [JsonPropertyName("relative_rmse_pct")]
    public double RelativeRmsePct { get; init; }

    [JsonPropertyName("relative_gap_vs_baseline_pct")]
    public double RelativeGapVsBaselinePct { get; init; }

    [JsonPropertyName("average_recent_rsi")]
    public double AverageRecentRsi { get; init; }

    [JsonPropertyName("beats_baseline_rmse")]
    public bool BeatsBaselineRmse { get; init; }
}

public sealed class BasketSummary
{
    [JsonPropertyName("basket_key")]
    public string BasketKey { get; init; } = string.Empty;

    [JsonPropertyName("basket_label")]
    public string BasketLabel { get; init; } = string.Empty;

    [JsonPropertyName("best_profile")]
    public string BestProfile { get; init; } = string.Empty;

    [JsonPropertyName("best_profile_label")]
    public string BestProfileLabel { get; init; } = string.Empty;

    [JsonPropertyName("mean_best_learned_rmse")]
    public double MeanBestLearnedRmse { get; init; }

    [JsonPropertyName("mean_walk_forward_baseline_rmse")]
    public double MeanWalkForwardBaselineRmse { get; init; }

    [JsonPropertyName("mean_gap_vs_baseline")]
    public double MeanGapVsBaseline { get; init; }

    [JsonPropertyName("dominant_best_model")]
    public string DominantBestModel { get; init; } = string.Empty;

    [JsonPropertyName("dominant_best_model_label")]
    public string DominantBestModelLabel { get; init; } = string.Empty;

    [JsonPropertyName("technical_extended_better_count")]
    public int TechnicalExtendedBetterCount { get; init; }

    [JsonPropertyName("lag_only_better_count")]
    public int LagOnlyBetterCount { get; init; }

    [JsonPropertyName("technical_extended_better_tickers")]
    public List<string> TechnicalExtendedBetterTickers { get; init; } = [];

    [JsonPropertyName("lag_only_better_tickers")]
    public List<string> LagOnlyBetterTickers { get; init; } = [];
}
