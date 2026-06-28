using Microsoft.AspNetCore.DataProtection;
using Microsoft.Extensions.Options;
using StockPredictor.App.Components;
using StockPredictor.App.Services;
using StockPredictor.App.Models;

var builder = WebApplication.CreateBuilder(args);
builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Logging.AddDebug();

// Add services to the container.
var dataProtectionKeyDirectory = Path.Combine(builder.Environment.ContentRootPath, ".data-protection-keys");
Directory.CreateDirectory(dataProtectionKeyDirectory);
builder.Services.AddDataProtection()
    .PersistKeysToFileSystem(new DirectoryInfo(dataProtectionKeyDirectory))
    .SetApplicationName("StockPredictor.App.Core");

builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();
builder.Services.Configure<ChatAssistantOptions>(builder.Configuration.GetSection(ChatAssistantOptions.SectionName));
builder.Services.Configure<MarketDataOptions>(builder.Configuration.GetSection(MarketDataOptions.SectionName));
builder.Services.Configure<ForecastAutomationOptions>(builder.Configuration.GetSection(ForecastAutomationOptions.SectionName));
builder.Services.Configure<NewsOptions>(builder.Configuration.GetSection(NewsOptions.SectionName));
builder.Services.AddSingleton<DashboardDataService>();
builder.Services.AddSingleton<AssetCatalogService>();
builder.Services.AddSingleton<ExplanationService>();
builder.Services.AddSingleton<LocalMlWorkspaceService>();
builder.Services.AddSingleton<MarketDataService>();
builder.Services.AddSingleton<ForecastJobService>();
builder.Services.AddScoped<NotificationService>();
builder.Services.AddHttpClient<RssNewsProvider>((serviceProvider, client) =>
{
    var newsOptions = serviceProvider.GetRequiredService<IOptions<NewsOptions>>().Value;
    client.Timeout = TimeSpan.FromSeconds(Math.Clamp(newsOptions.TimeoutSeconds, 5, 30));
    client.DefaultRequestHeaders.UserAgent.ParseAdd("stock-predictor-news/1.0");
});
builder.Services.AddSingleton<MockNewsProvider>();
builder.Services.AddSingleton<INewsProvider, ConfigurableNewsProvider>();
builder.Services.AddSingleton<NewsService>();
builder.Services.AddScoped<LocalUserProfileService>();
builder.Services.AddScoped<BrowserWatchlistService>();
builder.Services.AddHttpClient<OllamaChatAssistantService>((serviceProvider, client) =>
{
    var options = serviceProvider.GetRequiredService<IOptions<ChatAssistantOptions>>().Value;
    if (Uri.TryCreate(options.OllamaBaseUrl, UriKind.Absolute, out var baseUri))
    {
        client.BaseAddress = baseUri;
    }

    client.Timeout = TimeSpan.FromSeconds(Math.Clamp(options.RequestTimeoutSeconds, 5, 60));
});
builder.Services.AddScoped<MockChatAssistantService>();
builder.Services.AddScoped<IChatAssistantService, ChatAssistantRouterService>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}
app.UseStatusCodePagesWithReExecute("/not-found", createScopeForStatusCodePages: true);
app.UseHttpsRedirection();

app.UseAntiforgery();

app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
