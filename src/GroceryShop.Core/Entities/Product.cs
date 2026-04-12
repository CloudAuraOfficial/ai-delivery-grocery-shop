namespace GroceryShop.Core.Entities;

public class Product : BaseEntity
{
    public Guid CategoryId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string? Brand { get; set; }
    public decimal Price { get; set; }
    public string Unit { get; set; } = "each";
    public string? Weight { get; set; }
    public string? ImageUrl { get; set; }
    public string Sku { get; set; } = string.Empty;
    public bool IsAvailable { get; set; } = true;
    public bool IsOrganic { get; set; }
    public bool IsStoreBrand { get; set; }
    public string? NutritionInfo { get; set; }
    public string? Tags { get; set; }

    public Category Category { get; set; } = null!;
    public ICollection<Deal> Deals { get; set; } = new List<Deal>();
}
