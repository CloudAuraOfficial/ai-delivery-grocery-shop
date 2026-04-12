using GroceryShop.Infrastructure.Data;
using Microsoft.Azure.Functions.Worker;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var host = new HostBuilder()
    .ConfigureFunctionsWorkerDefaults()
    .ConfigureServices(services =>
    {
        var pgHost = Environment.GetEnvironmentVariable("POSTGRES_HOST") ?? "localhost";
        var pgPort = Environment.GetEnvironmentVariable("POSTGRES_PORT") ?? "5436";
        var pgDb = Environment.GetEnvironmentVariable("POSTGRES_DB") ?? "groceryshop";
        var pgUser = Environment.GetEnvironmentVariable("POSTGRES_USER") ?? "grocery";
        var pgPass = Environment.GetEnvironmentVariable("POSTGRES_PASSWORD") ?? "changeme";
        var conn = $"Host={pgHost};Port={pgPort};Database={pgDb};Username={pgUser};Password={pgPass}";

        services.AddDbContext<GroceryDbContext>(options => options.UseNpgsql(conn));
    })
    .Build();

host.Run();
