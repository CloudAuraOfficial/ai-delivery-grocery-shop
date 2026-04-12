using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace GroceryShop.Infrastructure.Data;

public class GroceryDbContextFactory : IDesignTimeDbContextFactory<GroceryDbContext>
{
    public GroceryDbContext CreateDbContext(string[] args)
    {
        var optionsBuilder = new DbContextOptionsBuilder<GroceryDbContext>();
        var host = Environment.GetEnvironmentVariable("POSTGRES_HOST") ?? "localhost";
        var port = Environment.GetEnvironmentVariable("POSTGRES_PORT") ?? "5436";
        var db = Environment.GetEnvironmentVariable("POSTGRES_DB") ?? "groceryshop";
        var user = Environment.GetEnvironmentVariable("POSTGRES_USER") ?? "grocery";
        var pass = Environment.GetEnvironmentVariable("POSTGRES_PASSWORD") ?? "changeme";

        optionsBuilder.UseNpgsql($"Host={host};Port={port};Database={db};Username={user};Password={pass}");
        return new GroceryDbContext(optionsBuilder.Options);
    }
}
