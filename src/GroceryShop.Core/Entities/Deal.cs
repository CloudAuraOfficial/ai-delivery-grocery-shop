using GroceryShop.Core.Enums;

namespace GroceryShop.Core.Entities;

public class Deal : BaseEntity
{
    public Guid ProductId { get; set; }
    public DealType DealType { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public decimal? DiscountPercent { get; set; }
    public decimal? DiscountAmount { get; set; }
    public int? BuyQuantity { get; set; }
    public int? GetQuantity { get; set; }
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
    public bool IsActive { get; set; } = true;

    public Product Product { get; set; } = null!;
}
