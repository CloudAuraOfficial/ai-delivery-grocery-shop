using GroceryShop.Api.Middleware;
using GroceryShop.Core.Interfaces;
using GroceryShop.Infrastructure.Data;
using GroceryShop.Infrastructure.Seed;
using GroceryShop.Infrastructure.Services;
using Microsoft.EntityFrameworkCore;
using Prometheus;

var builder = WebApplication.CreateBuilder(args);

// Configuration from environment variables
var pgHost = Environment.GetEnvironmentVariable("POSTGRES_HOST") ?? "localhost";
var pgPort = Environment.GetEnvironmentVariable("POSTGRES_PORT") ?? "5436";
var pgDb = Environment.GetEnvironmentVariable("POSTGRES_DB") ?? "groceryshop";
var pgUser = Environment.GetEnvironmentVariable("POSTGRES_USER") ?? "grocery";
var pgPass = Environment.GetEnvironmentVariable("POSTGRES_PASSWORD") ?? "changeme";
var connectionString = $"Host={pgHost};Port={pgPort};Database={pgDb};Username={pgUser};Password={pgPass}";

var allowedOrigins = Environment.GetEnvironmentVariable("CORS_ORIGINS")
    ?.Split(',', StringSplitOptions.RemoveEmptyEntries) ?? [];

// EF Core + PostgreSQL
builder.Services.AddDbContext<GroceryDbContext>(options =>
{
    options.UseNpgsql(connectionString);
});

// Services
builder.Services.AddScoped<ICategoryService, CategoryService>();
builder.Services.AddScoped<IProductService, ProductService>();
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
