using System.Text.Json;
using GroceryShop.Core.Models;

namespace GroceryShop.Api.Middleware;

public class ExceptionHandlerMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlerMiddleware> _logger;

    public ExceptionHandlerMiddleware(RequestDelegate next, ILogger<ExceptionHandlerMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unhandled exception on {Method} {Path}", context.Request.Method, context.Request.Path);

            context.Response.StatusCode = 500;
            context.Response.ContentType = "application/json";

            var error = new ErrorResponse
            {
                Error = "InternalServerError",
                Message = "An unexpected error occurred",
                StatusCode = 500
            };

            await context.Response.WriteAsync(JsonSerializer.Serialize(error));
        }
    }
}
