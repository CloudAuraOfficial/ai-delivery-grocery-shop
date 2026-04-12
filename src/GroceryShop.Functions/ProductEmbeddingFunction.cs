using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace GroceryShop.Functions;

public class ProductEmbeddingFunction
{
    private readonly ILogger<ProductEmbeddingFunction> _logger;

    public ProductEmbeddingFunction(ILogger<ProductEmbeddingFunction> logger)
    {
        _logger = logger;
    }

    [Function("ProductEmbedding")]
    public async Task Run(
        [QueueTrigger("product-embedding-queue", Connection = "AzureWebJobsStorage")] string message)
    {
        _logger.LogInformation("Product embedding triggered: {Message}", message);

        // Parse message: { "productId": "...", "action": "create|update|delete" }
        var payload = System.Text.Json.JsonSerializer.Deserialize<EmbeddingMessage>(message);
        if (payload == null) return;

        var aiServiceUrl = Environment.GetEnvironmentVariable("AI_SERVICE_URL") ?? "http://grocery-ai:8000";

        try
        {
            using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
            var content = new StringContent(
                System.Text.Json.JsonSerializer.Serialize(new { product_id = payload.ProductId, action = payload.Action }),
                System.Text.Encoding.UTF8,
                "application/json"
            );

            await http.PostAsync($"{aiServiceUrl}/api/embeddings/generate", content);
            _logger.LogInformation("Embedding {Action} for product {ProductId}", payload.Action, payload.ProductId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to process embedding for {ProductId}", payload.ProductId);
            throw; // Retry via queue visibility timeout
        }
    }

    private record EmbeddingMessage(string ProductId, string Action);
}
