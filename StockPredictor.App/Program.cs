using Microsoft.Extensions.Options;
using StockPredictor.App.Components;
using StockPredictor.App.Services;
using StockPredictor.App.Models;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();
builder.Services.Configure<ChatAssistantOptions>(builder.Configuration.GetSection(ChatAssistantOptions.SectionName));
builder.Services.AddSingleton<DashboardDataService>();
builder.Services.AddSingleton<AssetCatalogService>();
builder.Services.AddSingleton<ExplanationService>();
builder.Services.AddScoped<NotificationService>();
builder.Services.AddSingleton<INewsProvider, MockNewsProvider>();
builder.Services.AddSingleton<NewsService>();
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
