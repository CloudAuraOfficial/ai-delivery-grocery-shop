using GroceryShop.Core.DTOs;
using GroceryShop.Core.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace GroceryShop.Api.Controllers;

[ApiController]
[Route("api/v1/products")]
public class ProductsController : ControllerBase
{
    private readonly IProductService _productService;

    public ProductsController(IProductService productService) => _productService = productService;

    [HttpGet]
    public async Task<IActionResult> GetAll(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        [FromQuery] Guid? categoryId = null,
        [FromQuery] string? brand = null,
        [FromQuery] bool? isOrganic = null,
        [FromQuery] bool? dealsOnly = null,
        [FromQuery] string? sortBy = null)
    {
        var result = await _productService.GetProductsAsync(page, pageSize, categoryId, brand, isOrganic, dealsOnly, sortBy);
        return Ok(result);
    }

    [HttpGet("{id:guid}")]
    public async Task<IActionResult> GetById(Guid id)
    {
        var product = await _productService.GetProductByIdAsync(id);
        return product == null ? NotFound() : Ok(product);
    }

    [HttpGet("search")]
    public async Task<IActionResult> Search([FromQuery] string q, [FromQuery] int page = 1, [FromQuery] int pageSize = 20)
    {
        if (string.IsNullOrWhiteSpace(q))
            return BadRequest(new { error = "ValidationError", message = "Query parameter 'q' is required", statusCode = 400 });

        var result = await _productService.SearchProductsAsync(q, page, pageSize);
        return Ok(result);
    }

    [HttpGet("by-category/{slug}")]
    public async Task<IActionResult> GetByCategory(string slug, [FromQuery] int page = 1, [FromQuery] int pageSize = 20)
    {
        var result = await _productService.GetProductsByCategorySlugAsync(slug, page, pageSize);
        return Ok(result);
    }

    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateProductDto dto)
    {
        var product = await _productService.CreateProductAsync(dto);
        return CreatedAtAction(nameof(GetById), new { id = product.Id }, product);
    }

    [HttpPut("{id:guid}")]
    public async Task<IActionResult> Update(Guid id, [FromBody] CreateProductDto dto)
    {
        var product = await _productService.UpdateProductAsync(id, dto);
        return product == null ? NotFound() : Ok(product);
    }

    [HttpDelete("{id:guid}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        var result = await _productService.DeleteProductAsync(id);
        return result ? NoContent() : NotFound();
    }
}
