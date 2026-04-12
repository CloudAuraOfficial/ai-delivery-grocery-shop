namespace GroceryShop.Core.Entities;

public class StoreHours : BaseEntity
{
    public Guid StoreId { get; set; }
    public int DayOfWeek { get; set; }
    public TimeOnly OpenTime { get; set; }
    public TimeOnly CloseTime { get; set; }

    public Store Store { get; set; } = null!;
}
