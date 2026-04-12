namespace GroceryShop.Core.DTOs;

public record StoreDto(
    Guid Id,
    string Name,
    string StoreNumber,
    string Address,
    string City,
    string State,
    string ZipCode,
    string Phone,
    decimal Latitude,
    decimal Longitude,
    bool IsOpen,
    IReadOnlyList<StoreHoursDto> Hours
);

public record StoreHoursDto(
    int DayOfWeek,
    string DayName,
    string OpenTime,
    string CloseTime
);
