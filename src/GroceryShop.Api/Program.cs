using GroceryShop.Api.Middleware;
using GroceryShop.Core.Interfaces;
using GroceryShop.Infrastructure.Data;
using GroceryShop.Infrastructure.Seed;
using GroceryShop.Infrastructure.Services;
using Microsoft.EntityFrameworkCore;
using Prometheus;
using StackExchange.Redis;

var builder = WebApplication.CreateBuilder(args);

// Configuration from environment variables
var pgHost = Environment.GetEnvironmentVariable("POSTGRES_HOST") ?? "localhost";
var pgPort = Environment.GetEnvironmentVariable("POSTGRES_PORT") ?? "5436";
var pgDb = Environment.GetEnvironmentVariable("POSTGRES_DB") ?? "groceryshop";
var pgUser = Environment.GetEnvironmentVariable("POSTGRES_USER") ?? "grocery";
var pgPass = Environment.GetEnvironmentVariable("POSTGRES_PASSWORD") ?? "changeme";
var connectionString = $"Host={pgHost};Port={pgPort};Database={pgDb};Username={pgUser};Password={pgPass}";

var redisHost = Environment.GetEnvironmentVariable("REDIS_HOST") ?? "localhost";
var redisPort = Environment.GetEnvironmentVariable("REDIS_PORT") ?? "6380";

var allowedOrigins = Environment.GetEnvironmentVariable("CORS_ORIGINS")
    ?.Split(',', StringSplitOptions.RemoveEmptyEntries) ?? [];

// EF Core + PostgreSQL
builder.Services.AddDbContext<GroceryDbContext>(options =>
{
    options.UseNpgsql(connectionString);
});

// Redis
builder.Services.AddSingleton<IConnectionMultiplexer>(
    ConnectionMultiplexer.Connect($"{redisHost}:{redisPort},abortConnect=false"));

// Services
builder.Services.AddScoped<ICategoryService, CategoryService>();
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddScoped<IDealService, DealService>();
builder.Services.AddScoped<IStoreService, StoreService>();
builder.Services.AddScoped<ICartService, CartService>();
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddScoped<SeedDataService>();

// CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        if (allowedOrigins.Length > 0)
            policy.WithOrigins(allowedOrigins);
        else
            policy.AllowAnyOrigin();

        policy.AllowAnyHeader().AllowAnyMethod();
    });
});

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Seed database on startup
using (var scope = app.Services.CreateScope())
{
    var seeder = scope.ServiceProvider.GetRequiredService<SeedDataService>();
    await seeder.SeedAsync();
}

// Middleware pipeline
app.UseMiddleware<ExceptionHandlerMiddleware>();
app.UseCors();

app.UseSwagger();
app.UseSwaggerUI();

app.MapControllers();
app.MapMetrics();

app.Run();
