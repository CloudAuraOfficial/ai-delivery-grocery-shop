using GroceryShop.Core.Entities;
using Microsoft.EntityFrameworkCore;

namespace GroceryShop.Infrastructure.Data;

public class GroceryDbContext : DbContext
{
    public GroceryDbContext(DbContextOptions<GroceryDbContext> options) : base(options) { }

    public DbSet<Category> Categories => Set<Category>();
    public DbSet<Product> Products => Set<Product>();
    public DbSet<Deal> Deals => Set<Deal>();
    public DbSet<Store> Stores => Set<Store>();
    public DbSet<StoreHours> StoreHours => Set<StoreHours>();
    public DbSet<User> Users => Set<User>();
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();
    public DbSet<ChatSession> ChatSessions => Set<ChatSession>();
    public DbSet<ChatMessage> ChatMessages => Set<ChatMessage>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Category
        modelBuilder.Entity<Category>(b =>
        {
            b.HasIndex(c => c.Slug).IsUnique();
            b.HasIndex(c => c.Name).IsUnique();
            b.Property(c => c.Name).HasMaxLength(100);
            b.Property(c => c.Slug).HasMaxLength(100);
            b.Property(c => c.Description).HasMaxLength(500);
            b.Property(c => c.ImageUrl).HasMaxLength(500);
        });

        // Product
        modelBuilder.Entity<Product>(b =>
        {
            b.HasIndex(p => p.Slug).IsUnique();
            b.HasIndex(p => p.Sku).IsUnique();
            b.HasIndex(p => p.CategoryId);
            b.HasIndex(p => new { p.IsAvailable, p.CategoryId });
            b.Property(p => p.Name).HasMaxLength(200);
            b.Property(p => p.Slug).HasMaxLength(200);
            b.Property(p => p.Description).HasMaxLength(1000);
            b.Property(p => p.Brand).HasMaxLength(100);
            b.Property(p => p.Price).HasPrecision(10, 2);
            b.Property(p => p.Unit).HasMaxLength(20);
            b.Property(p => p.Weight).HasMaxLength(50);
            b.Property(p => p.ImageUrl).HasMaxLength(500);
            b.Property(p => p.Sku).HasMaxLength(50);
            b.Property(p => p.Tags).HasMaxLength(500);
            b.HasOne(p => p.Category).WithMany(c => c.Products).HasForeignKey(p => p.CategoryId);
        });

        // Deal
        modelBuilder.Entity<Deal>(b =>
        {
            b.HasIndex(d => new { d.ProductId, d.IsActive });
            b.HasIndex(d => new { d.DealType, d.IsActive, d.EndDate });
            b.Property(d => d.Title).HasMaxLength(200);
            b.Property(d => d.Description).HasMaxLength(500);
            b.Property(d => d.DiscountPercent).HasPrecision(5, 2);
            b.Property(d => d.DiscountAmount).HasPrecision(10, 2);
            b.Property(d => d.DealType).HasConversion<string>().HasMaxLength(20);
            b.HasOne(d => d.Product).WithMany(p => p.Deals).HasForeignKey(d => d.ProductId);
        });

        // Store
        modelBuilder.Entity<Store>(b =>
        {
            b.HasIndex(s => s.StoreNumber).IsUnique();
            b.HasIndex(s => s.ZipCode);
            b.Property(s => s.Name).HasMaxLength(200);
            b.Property(s => s.StoreNumber).HasMaxLength(10);
            b.Property(s => s.Address).HasMaxLength(300);
            b.Property(s => s.City).HasMaxLength(100);
            b.Property(s => s.State).HasMaxLength(2);
            b.Property(s => s.ZipCode).HasMaxLength(10);
            b.Property(s => s.Phone).HasMaxLength(20);
            b.Property(s => s.Latitude).HasPrecision(10, 7);
            b.Property(s => s.Longitude).HasPrecision(10, 7);
        });

        // StoreHours
        modelBuilder.Entity<StoreHours>(b =>
        {
            b.HasOne(h => h.Store).WithMany(s => s.Hours).HasForeignKey(h => h.StoreId);
        });

        // User
        modelBuilder.Entity<User>(b =>
        {
            b.HasIndex(u => u.Email).IsUnique();
            b.Property(u => u.Email).HasMaxLength(256);
            b.Property(u => u.DisplayName).HasMaxLength(100);
            b.Property(u => u.PasswordHash).HasMaxLength(500);
            b.HasOne(u => u.PreferredStore).WithMany().HasForeignKey(u => u.PreferredStoreId);
        });

        // Order
        modelBuilder.Entity<Order>(b =>
        {
            b.HasIndex(o => o.OrderNumber).IsUnique();
            b.HasIndex(o => new { o.UserId, o.CreatedAt });
            b.HasIndex(o => new { o.StoreId, o.Status });
            b.Property(o => o.OrderNumber).HasMaxLength(20);
            b.Property(o => o.Status).HasConversion<string>().HasMaxLength(20);
            b.Property(o => o.SubTotal).HasPrecision(10, 2);
            b.Property(o => o.Tax).HasPrecision(10, 2);
            b.Property(o => o.DeliveryFee).HasPrecision(10, 2);
            b.Property(o => o.Total).HasPrecision(10, 2);
            b.Property(o => o.DeliveryAddress).HasMaxLength(500);
            b.Property(o => o.Notes).HasMaxLength(500);
            b.HasOne(o => o.User).WithMany(u => u.Orders).HasForeignKey(o => o.UserId);
            b.HasOne(o => o.Store).WithMany(s => s.Orders).HasForeignKey(o => o.StoreId);
        });

        // OrderItem
        modelBuilder.Entity<OrderItem>(b =>
        {
            b.Property(i => i.UnitPrice).HasPrecision(10, 2);
            b.Property(i => i.LineTotal).HasPrecision(10, 2);
            b.HasOne(i => i.Order).WithMany(o => o.Items).HasForeignKey(i => i.OrderId);
            b.HasOne(i => i.Product).WithMany().HasForeignKey(i => i.ProductId);
            b.HasOne(i => i.Deal).WithMany().HasForeignKey(i => i.DealId);
        });

        // ChatSession
        modelBuilder.Entity<ChatSession>(b =>
        {
            b.HasIndex(s => s.SessionToken).IsUnique();
            b.Property(s => s.SessionToken).HasMaxLength(100);
            b.HasOne(s => s.User).WithMany(u => u.ChatSessions).HasForeignKey(s => s.UserId);
        });

        // ChatMessage
        modelBuilder.Entity<ChatMessage>(b =>
        {
            b.HasIndex(m => new { m.SessionId, m.CreatedAt });
            b.Property(m => m.Role).HasMaxLength(20);
            b.Property(m => m.LatencyMs).HasPrecision(10, 1);
            b.Property(m => m.Model).HasMaxLength(100);
            b.HasOne(m => m.Session).WithMany(s => s.Messages).HasForeignKey(m => m.SessionId);
        });
    }

    public override Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        foreach (var entry in ChangeTracker.Entries<BaseEntity>())
        {
            if (entry.State == EntityState.Modified)
                entry.Entity.UpdatedAt = DateTime.UtcNow;
        }
        return base.SaveChangesAsync(cancellationToken);
    }
}
