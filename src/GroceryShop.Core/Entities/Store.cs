namespace GroceryShop.Core.Entities;

public class Store : BaseEntity
{
    public string Name { get; set; } = string.Empty;
    public string StoreNumber { get; set; } = string.Empty;
    public string Address { get; set; } = string.Empty;
    public string City { get; set; } = string.Empty;
    public string State { get; set; } = "FL";
    public string ZipCode { get; set; } = string.Empty;
    public string Phone { get; set; } = string.Empty;
    public decimal Latitude { get; set; }
    public decimal Longitude { get; set; }
    public bool IsOpen { get; set; } = true;

    public ICollection<StoreHours> Hours { get; set; } = new List<StoreHours>();
    public ICollection<Order> Orders { get; set; } = new List<Order>();
}
