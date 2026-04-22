using GroceryShop.Api.Tests.Helpers;
using GroceryShop.Core.DTOs;
using GroceryShop.Core.Enums;
using GroceryShop.Infrastructure.Data;
using GroceryShop.Infrastructure.Services;
using Moq;

namespace GroceryShop.Api.Tests.Services;

public class OrderServiceTests : IAsyncDisposable
{
    private readonly GroceryDbContext _db;
    private readonly Mock<Core.Interfaces.ICartService> _cartServiceMock;
    private readonly OrderService _sut;

    public OrderServiceTests()
    {
        _db = TestDbContextFactory.Create();
        _cartServiceMock = new Mock<Core.Interfaces.ICartService>();
        _sut = new OrderService(_db, _cartServiceMock.Object);
    }

    public async ValueTask DisposeAsync()
    {
        await _db.DisposeAsync();
    }

    private void SetupCartWithItems(decimal subTotal, params CartItemDto[] items)
    {
        var tax = Math.Round(subTotal * 0.07m, 2);
        var deliveryFee = subTotal >= 35m ? 0m : 5.99m;
        var total = subTotal + tax + deliveryFee;
        var itemCount = items.Sum(i => i.Quantity);

        var cart = new CartDto(items, subTotal, tax, deliveryFee, total, itemCount);

        _cartServiceMock.Setup(c => c.GetCartAsync(It.IsAny<string>()))
            .ReturnsAsync(cart);
        _cartServiceMock.Setup(c => c.ClearCartAsync(It.IsAny<string>()))
            .Returns(Task.CompletedTask);
    }

    private void SetupEmptyCart()
    {
        _cartServiceMock.Setup(c => c.GetCartAsync(It.IsAny<string>()))
            .ReturnsAsync(new CartDto([], 0, 0, 0, 0, 0));
    }

    // ─── CreateOrderAsync ────────────────────────────────────

    [Fact]
    public async Task CreateOrder_FromPopulatedCart_CreatesOrderWithItems()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var cartItems = new[]
        {
            new CartItemDto(TestData.AppleId, "Organic Fuji Apple", 1.99m, 3, 5.97m, null),
            new CartItemDto(TestData.WaterId, "Spring Water", 4.99m, 1, 4.99m, null)
        };
        SetupCartWithItems(10.96m, cartItems);

        var dto = new CreateOrderDto(TestData.StoreId, "123 Main St, Lakeland FL", "Leave at door");

        var result = await _sut.CreateOrderAsync(TestData.UserId, "session-1", dto);

        Assert.NotNull(result);
        Assert.StartsWith("ORD-", result.OrderNumber);
        Assert.Equal(OrderStatus.Pending, result.Status);
        Assert.Equal(10.96m, result.SubTotal);
        Assert.Equal("123 Main St, Lakeland FL", result.DeliveryAddress);
        Assert.Equal(2, result.Items.Count);
    }

    [Fact]
    public async Task CreateOrder_GeneratesUniqueOrderNumber()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var cartItems = new[]
        {
            new CartItemDto(TestData.AppleId, "Apple", 1.99m, 1, 1.99m, null)
        };
        SetupCartWithItems(1.99m, cartItems);

        var dto = new CreateOrderDto(TestData.StoreId, "123 Main St", null);

        var order1 = await _sut.CreateOrderAsync(TestData.UserId, "s1", dto);

        // Reset cart mock for second order
        SetupCartWithItems(1.99m, cartItems);
        var order2 = await _sut.CreateOrderAsync(TestData.UserId, "s2", dto);

        Assert.NotEqual(order1.OrderNumber, order2.OrderNumber);
    }

    [Fact]
    public async Task CreateOrder_SetsEstimatedDelivery_45MinutesFromNow()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var cartItems = new[]
        {
            new CartItemDto(TestData.AppleId, "Apple", 1.99m, 1, 1.99m, null)
        };
        SetupCartWithItems(1.99m, cartItems);

        var before = DateTime.UtcNow.AddMinutes(44);
        var result = await _sut.CreateOrderAsync(TestData.UserId, "s1",
            new CreateOrderDto(TestData.StoreId, "123 Main St", null));
        var after = DateTime.UtcNow.AddMinutes(46);

        Assert.NotNull(result.EstimatedDelivery);
        Assert.InRange(result.EstimatedDelivery.Value, before, after);
    }

    // ─── Interview: empty cart guard ─────────────────────────

    [Fact]
    public async Task CreateOrder_EmptyCart_ThrowsInvalidOperationException()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);
        SetupEmptyCart();

        var dto = new CreateOrderDto(TestData.StoreId, "123 Main St", null);

        await Assert.ThrowsAsync<InvalidOperationException>(
            () => _sut.CreateOrderAsync(TestData.UserId, "session-1", dto));
    }

    // ─── Interview: cart cleared after order ─────────────────

    [Fact]
    public async Task CreateOrder_ClearsCartAfterSaving()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var cartItems = new[]
        {
            new CartItemDto(TestData.AppleId, "Apple", 1.99m, 1, 1.99m, null)
        };
        SetupCartWithItems(1.99m, cartItems);

        await _sut.CreateOrderAsync(TestData.UserId, "session-1",
            new CreateOrderDto(TestData.StoreId, "123 Main St", null));

        _cartServiceMock.Verify(c => c.ClearCartAsync("session-1"), Times.Once);
    }

    // ─── UpdateOrderStatusAsync ──────────────────────────────

    [Fact]
    public async Task UpdateOrderStatus_ValidTransition_UpdatesStatus()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var cartItems = new[]
        {
            new CartItemDto(TestData.AppleId, "Apple", 1.99m, 1, 1.99m, null)
        };
        SetupCartWithItems(1.99m, cartItems);

        var order = await _sut.CreateOrderAsync(TestData.UserId, "s1",
            new CreateOrderDto(TestData.StoreId, "123 Main St", null));

        var updated = await _sut.UpdateOrderStatusAsync(order.Id, OrderStatus.Confirmed);

        Assert.NotNull(updated);
        Assert.Equal(OrderStatus.Confirmed, updated.Status);
    }

    [Fact]
    public async Task UpdateOrderStatus_FullLifecycle_Pending_To_Delivered()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var cartItems = new[]
        {
            new CartItemDto(TestData.AppleId, "Apple", 1.99m, 1, 1.99m, null)
        };
        SetupCartWithItems(1.99m, cartItems);

        var order = await _sut.CreateOrderAsync(TestData.UserId, "s1",
            new CreateOrderDto(TestData.StoreId, "123 Main St", null));

        // Walk through the full order lifecycle
        var confirmed = await _sut.UpdateOrderStatusAsync(order.Id, OrderStatus.Confirmed);
        Assert.Equal(OrderStatus.Confirmed, confirmed!.Status);

        var preparing = await _sut.UpdateOrderStatusAsync(order.Id, OrderStatus.Preparing);
        Assert.Equal(OrderStatus.Preparing, preparing!.Status);

        var delivering = await _sut.UpdateOrderStatusAsync(order.Id, OrderStatus.Delivering);
        Assert.Equal(OrderStatus.Delivering, delivering!.Status);

        var delivered = await _sut.UpdateOrderStatusAsync(order.Id, OrderStatus.Delivered);
        Assert.Equal(OrderStatus.Delivered, delivered!.Status);
    }

    [Fact]
    public async Task UpdateOrderStatus_NonExistentOrder_ReturnsNull()
    {
        var result = await _sut.UpdateOrderStatusAsync(Guid.NewGuid(), OrderStatus.Confirmed);

        Assert.Null(result);
    }

    // ─── GetOrdersAsync ──────────────────────────────────────

    [Fact]
    public async Task GetOrders_ReturnsOnlyUserOrders()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var cartItems = new[]
        {
            new CartItemDto(TestData.AppleId, "Apple", 1.99m, 1, 1.99m, null)
        };
        SetupCartWithItems(1.99m, cartItems);

        await _sut.CreateOrderAsync(TestData.UserId, "s1",
            new CreateOrderDto(TestData.StoreId, "Address 1", null));

        SetupCartWithItems(1.99m, cartItems);
        await _sut.CreateOrderAsync(TestData.UserId, "s2",
            new CreateOrderDto(TestData.StoreId, "Address 2", null));

        var result = await _sut.GetOrdersAsync(TestData.UserId, 1, 20);

        Assert.Equal(2, result.TotalCount);

        // Different user sees nothing
        var otherResult = await _sut.GetOrdersAsync(Guid.NewGuid(), 1, 20);
        Assert.Equal(0, otherResult.TotalCount);
    }

    [Fact]
    public async Task GetOrders_OrderedByCreatedAtDescending()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var cartItems = new[]
        {
            new CartItemDto(TestData.AppleId, "Apple", 1.99m, 1, 1.99m, null)
        };

        SetupCartWithItems(1.99m, cartItems);
        await _sut.CreateOrderAsync(TestData.UserId, "s1",
            new CreateOrderDto(TestData.StoreId, "First", null));

        SetupCartWithItems(1.99m, cartItems);
        await _sut.CreateOrderAsync(TestData.UserId, "s2",
            new CreateOrderDto(TestData.StoreId, "Second", null));

        var result = await _sut.GetOrdersAsync(TestData.UserId, 1, 20);

        // Most recent first
        Assert.True(result.Items[0].CreatedAt >= result.Items[1].CreatedAt);
    }

    // ─── GetOrderByIdAsync ───────────────────────────────────

    [Fact]
    public async Task GetOrderById_ExistingOrder_IncludesItems()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var cartItems = new[]
        {
            new CartItemDto(TestData.AppleId, "Organic Fuji Apple", 1.99m, 2, 3.98m, null),
            new CartItemDto(TestData.WaterId, "Spring Water", 4.99m, 1, 4.99m, null)
        };
        SetupCartWithItems(8.97m, cartItems);

        var order = await _sut.CreateOrderAsync(TestData.UserId, "s1",
            new CreateOrderDto(TestData.StoreId, "123 Main St", null));

        var result = await _sut.GetOrderByIdAsync(order.Id);

        Assert.NotNull(result);
        Assert.Equal(2, result.Items.Count);
        Assert.Contains(result.Items, i => i.ProductName == "Organic Fuji Apple" && i.Quantity == 2);
    }

    [Fact]
    public async Task GetOrderById_NonExistent_ReturnsNull()
    {
        var result = await _sut.GetOrderByIdAsync(Guid.NewGuid());

        Assert.Null(result);
    }
}
