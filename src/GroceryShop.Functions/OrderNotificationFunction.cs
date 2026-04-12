using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace GroceryShop.Functions;

public class OrderNotificationFunction
{
    private readonly ILogger<OrderNotificationFunction> _logger;

    public OrderNotificationFunction(ILogger<OrderNotificationFunction> logger)
    {
        _logger = logger;
    }

    [Function("OrderNotification")]
    public Task Run(
        [QueueTrigger("order-notification-queue", Connection = "AzureWebJobsStorage")] string message)
    {
        _logger.LogInformation("Order notification triggered: {Message}", message);

        var payload = System.Text.Json.JsonSerializer.Deserialize<OrderNotificationMessage>(message);
        if (payload == null) return Task.CompletedTask;

        // In production: send email/SMS notification
        // For demo: log the status change
        _logger.LogInformation(
            "Order {OrderId} status changed to {Status} for user {UserId}",
            payload.OrderId, payload.NewStatus, payload.UserId
        );

        return Task.CompletedTask;
    }

    private record OrderNotificationMessage(string OrderId, string NewStatus, string UserId);
}
