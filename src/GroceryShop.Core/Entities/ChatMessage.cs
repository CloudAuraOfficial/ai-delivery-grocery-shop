namespace GroceryShop.Core.Entities;

public class ChatMessage : BaseEntity
{
    public Guid SessionId { get; set; }
    public string Role { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public string? RetrievedProductIds { get; set; }
    public decimal? LatencyMs { get; set; }
    public string? Model { get; set; }

    public ChatSession Session { get; set; } = null!;
}
