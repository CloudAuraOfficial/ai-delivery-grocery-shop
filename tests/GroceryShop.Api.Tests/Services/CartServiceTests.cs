using System.Text.Json;
using GroceryShop.Api.Tests.Helpers;
using GroceryShop.Core.DTOs;
using GroceryShop.Infrastructure.Data;
using GroceryShop.Infrastructure.Services;
using Moq;
using StackExchange.Redis;

namespace GroceryShop.Api.Tests.Services;

public class CartServiceTests : IAsyncDisposable
{
    private readonly GroceryDbContext _db;
    private readonly Mock<IConnectionMultiplexer> _redisMock;
    private readonly Mock<IDatabase> _redisDbMock;
    private readonly CartService _sut;

    // Simulated Redis store
    private readonly Dictionary<string, (string Value, TimeSpan? Expiry)> _redisStore = new();

    public CartServiceTests()
    {
        _db = TestDbContextFactory.Create();
        _redisMock = new Mock<IConnectionMultiplexer>();
        _redisDbMock = new Mock<IDatabase>();
        _redisMock.Setup(r => r.GetDatabase(It.IsAny<int>(), It.IsAny<object>()))
            .Returns(_redisDbMock.Object);

        // Mock StringGetAsync: return value from in-memory store
        _redisDbMock.Setup(d => d.StringGetAsync(It.IsAny<RedisKey>(), It.IsAny<CommandFlags>()))
            .ReturnsAsync((RedisKey key, CommandFlags _) =>
                _redisStore.TryGetValue(key.ToString(), out var entry)
                    ? (RedisValue)entry.Value
                    : RedisValue.Null);

        // Mock StringSetAsync: store in memory
        _redisDbMock.Setup(d => d.StringSetAsync(
                It.IsAny<RedisKey>(), It.IsAny<RedisValue>(),
                It.IsAny<TimeSpan?>(), It.IsAny<bool>(),
                It.IsAny<When>(), It.IsAny<CommandFlags>()))
            .ReturnsAsync((RedisKey key, RedisValue value, TimeSpan? expiry,
                bool _, When __, CommandFlags ___) =>
            {
                _redisStore[key.ToString()] = (value.ToString(), expiry);
                return true;
            });

        // Mock KeyDeleteAsync
        _redisDbMock.Setup(d => d.KeyDeleteAsync(It.IsAny<RedisKey>(), It.IsAny<CommandFlags>()))
            .ReturnsAsync((RedisKey key, CommandFlags _) => _redisStore.Remove(key.ToString()));

        _sut = new CartService(_redisMock.Object, _db);
    }

    public async ValueTask DisposeAsync()
    {
        await _db.DisposeAsync();
    }

    // ─── GetCartAsync ────────────────────────────────────────

    [Fact]
    public async Task GetCart_EmptySession_ReturnsEmptyCart()
    {
        var cart = await _sut.GetCartAsync("new-session");

        Assert.Empty(cart.Items);
        Assert.Equal(0m, cart.SubTotal);
        Assert.Equal(0m, cart.Total);
        Assert.Equal(0, cart.ItemCount);
    }

    // ─── AddItemAsync ───────��───────────────────────────────���

    [Fact]
    public async Task AddItem_NewProduct_AddsToCart()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var cart = await _sut.AddItemAsync("session-1",
            new AddToCartDto(TestData.AppleId, 3));

        Assert.Single(cart.Items);
        Assert.Equal(TestData.AppleId, cart.Items[0].ProductId);
        Assert.Equal(3, cart.Items[0].Quantity);
        Assert.Equal(1.99m * 3, cart.Items[0].LineTotal);
    }

    [Fact]
    public async Task AddItem_ExistingProduct_IncrementsQuantity()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        await _sut.AddItemAsync("session-1", new AddToCartDto(TestData.AppleId, 2));
        var cart = await _sut.AddItemAsync("session-1", new AddToCartDto(TestData.AppleId, 3));

        Assert.Single(cart.Items);
        Assert.Equal(5, cart.Items[0].Quantity); // 2 + 3
    }

    [Fact]
    public async Task AddItem_MultipleProducts_TracksAll()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        await _sut.AddItemAsync("session-1", new AddToCartDto(TestData.AppleId, 1));
        var cart = await _sut.AddItemAsync("session-1", new AddToCartDto(TestData.WaterId, 2));

        Assert.Equal(2, cart.Items.Count);
        Assert.Equal(3, cart.ItemCount); // 1 + 2
    }

    // ─── Tax and Delivery Fee Calculation ────────────────────
    // Interview topic: business logic in service layer

    [Fact]
    public async Task Cart_TaxCalculation_SevenPercentFloridaSalesTax()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        // 10 apples at $1.99 = $19.90 subtotal
        var cart = await _sut.AddItemAsync("session-1",
            new AddToCartDto(TestData.AppleId, 10));

        var expectedTax = Math.Round(19.90m * 0.07m, 2); // $1.39
        Assert.Equal(expectedTax, cart.EstimatedTax);
    }

    [Fact]
    public async Task Cart_DeliveryFee_FreeOver35Dollars()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        // 20 apples at $1.99 = $39.80 subtotal (> $35)
        var cart = await _sut.AddItemAsync("session-1",
            new AddToCartDto(TestData.AppleId, 20));

        Assert.Equal(0m, cart.DeliveryFee);
    }

    [Fact]
    public async Task Cart_DeliveryFee_ChargedUnder35Dollars()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        // 1 apple at $1.99 (< $35)
        var cart = await _sut.AddItemAsync("session-1",
            new AddToCartDto(TestData.AppleId, 1));

        Assert.Equal(5.99m, cart.DeliveryFee);
    }

    [Fact]
    public async Task Cart_TotalCalculation_SubTotalPlusTaxPlusDelivery()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        // 1 apple = $1.99
        var cart = await _sut.AddItemAsync("session-1",
            new AddToCartDto(TestData.AppleId, 1));

        var expectedSubTotal = 1.99m;
        var expectedTax = Math.Round(expectedSubTotal * 0.07m, 2);
        var expectedDelivery = 5.99m; // under $35
        var expectedTotal = expectedSubTotal + expectedTax + expectedDelivery;

        Assert.Equal(expectedSubTotal, cart.SubTotal);
        Assert.Equal(expectedTax, cart.EstimatedTax);
        Assert.Equal(expectedDelivery, cart.DeliveryFee);
        Assert.Equal(expectedTotal, cart.Total);
    }

    // ─── UpdateItemAsync ─────────────────────────────────────

    [Fact]
    public async Task UpdateItem_ChangesQuantity()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);
        await _sut.AddItemAsync("session-1", new AddToCartDto(TestData.AppleId, 5));

        var cart = await _sut.UpdateItemAsync("session-1",
            TestData.AppleId, new UpdateCartItemDto(2));

        Assert.Single(cart.Items);
        Assert.Equal(2, cart.Items[0].Quantity);
    }

    [Fact]
    public async Task UpdateItem_ZeroQuantity_RemovesItem()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);
        await _sut.AddItemAsync("session-1", new AddToCartDto(TestData.AppleId, 3));

        var cart = await _sut.UpdateItemAsync("session-1",
            TestData.AppleId, new UpdateCartItemDto(0));

        Assert.Empty(cart.Items);
    }

    // ─── RemoveItemAsync ─────────────────────────────────────

    [Fact]
    public async Task RemoveItem_ExistingProduct_RemovesFromCart()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);
        await _sut.AddItemAsync("session-1", new AddToCartDto(TestData.AppleId, 1));
        await _sut.AddItemAsync("session-1", new AddToCartDto(TestData.WaterId, 1));

        var cart = await _sut.RemoveItemAsync("session-1", TestData.AppleId);

        Assert.Single(cart.Items);
        Assert.Equal(TestData.WaterId, cart.Items[0].ProductId);
    }

    // ─── ClearCartAsync ────���─────────────────────────────��───

    [Fact]
    public async Task ClearCart_RemovesRedisKey()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);
        await _sut.AddItemAsync("session-1", new AddToCartDto(TestData.AppleId, 5));

        await _sut.ClearCartAsync("session-1");

        var cart = await _sut.GetCartAsync("session-1");
        Assert.Empty(cart.Items);
    }

    // ─── Redis TTL (Interview: session expiry) ───────────────

    [Fact]
    public async Task AddItem_SetsRedisTTL_24Hours()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        await _sut.AddItemAsync("session-ttl", new AddToCartDto(TestData.AppleId, 1));

        // Verify StringSetAsync was called with 24-hour expiry
        _redisDbMock.Verify(d => d.StringSetAsync(
            It.Is<RedisKey>(k => k.ToString() == "cart:session-ttl"),
            It.IsAny<RedisValue>(),
            It.Is<TimeSpan?>(t => t.HasValue && t.Value.TotalHours == 24),
            It.IsAny<bool>(),
            It.IsAny<When>(),
            It.IsAny<CommandFlags>()),
            Times.Once);
    }

    // ─── Session isolation (Interview: multi-tenant safety) ──

    [Fact]
    public async Task DifferentSessions_HaveIndependentCarts()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        await _sut.AddItemAsync("user-A", new AddToCartDto(TestData.AppleId, 3));
        await _sut.AddItemAsync("user-B", new AddToCartDto(TestData.WaterId, 1));

        var cartA = await _sut.GetCartAsync("user-A");
        var cartB = await _sut.GetCartAsync("user-B");

        Assert.Single(cartA.Items);
        Assert.Equal(TestData.AppleId, cartA.Items[0].ProductId);
        Assert.Single(cartB.Items);
        Assert.Equal(TestData.WaterId, cartB.Items[0].ProductId);
    }

    // ─── Interview: deal attached to cart item ───────────────

    [Fact]
    public async Task AddItem_WithActiveDeal_IncludesDealInCartItem()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var cart = await _sut.AddItemAsync("session-1",
            new AddToCartDto(TestData.AppleId, 1));

        Assert.NotNull(cart.Items[0].AppliedDeal);
        Assert.Equal("25% Off Organic Apples", cart.Items[0].AppliedDeal.Title);
    }

    [Fact]
    public async Task AddItem_WithNoDeal_NullDealOnCartItem()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var cart = await _sut.AddItemAsync("session-1",
            new AddToCartDto(TestData.WaterId, 1));

        Assert.Null(cart.Items[0].AppliedDeal);
    }
}
