namespace GroceryShop.Core.Entities;

public class ChatSession : BaseEntity
{
    public Guid? UserId { get; set; }
    public string SessionToken { get; set; } = string.Empty;
    public DateTime? LastMessageAt { get; set; }

    public User? User { get; set; }
    public ICollection<ChatMessage> Messages { get; set; } = new List<ChatMessage>();
}
