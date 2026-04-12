using GroceryShop.Core.Enums;

namespace GroceryShop.Core.Entities;

public class Order : BaseEntity
{
    public Guid UserId { get; set; }
    public Guid StoreId { get; set; }
    public string OrderNumber { get; set; } = string.Empty;
    public OrderStatus Status { get; set; } = OrderStatus.Pending;
    public decimal SubTotal { get; set; }
    public decimal Tax { get; set; }
    public decimal DeliveryFee { get; set; }
    public decimal Total { get; set; }
    public string DeliveryAddress { get; set; } = string.Empty;
    public string? Notes { get; set; }
    public DateTime? EstimatedDelivery { get; set; }

    public User User { get; set; } = null!;
    public Store Store { get; set; } = null!;
    public ICollection<OrderItem> Items { get; set; } = new List<OrderItem>();
}
