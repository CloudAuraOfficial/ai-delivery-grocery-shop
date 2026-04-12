namespace GroceryShop.Core.Entities;

public class User : BaseEntity
{
    public string Email { get; set; } = string.Empty;
    public string DisplayName { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public Guid? PreferredStoreId { get; set; }

    public Store? PreferredStore { get; set; }
    public ICollection<Order> Orders { get; set; } = new List<Order>();
    public ICollection<ChatSession> ChatSessions { get; set; } = new List<ChatSession>();
}
