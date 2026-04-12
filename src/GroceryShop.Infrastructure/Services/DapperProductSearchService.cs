using Dapper;
using GroceryShop.Core.DTOs;
using GroceryShop.Core.Models;
using Npgsql;

namespace GroceryShop.Infrastructure.Services;

public class DapperProductSearchService
{
    private readonly string _connectionString;

    public DapperProductSearchService(string connectionString) => _connectionString = connectionString;

    public async Task<PagedResult<ProductDto>> FullTextSearchAsync(string query, int page, int pageSize)
    {
        await using var conn = new NpgsqlConnection(_connectionString);

        var searchTerm = $"%{query.ToLower()}%";
        var offset = (page - 1) * pageSize;

        const string countSql = """
            SELECT COUNT(*) FROM "Products" p
            JOIN "Categories" c ON p."CategoryId" = c."Id"
            WHERE p."IsAvailable" = true
            AND (LOWER(p."Name") LIKE @Search
                 OR LOWER(p."Description") LIKE @Search
                 OR LOWER(COALESCE(p."Brand", '')) LIKE @Search
                 OR LOWER(COALESCE(p."Tags", '')) LIKE @Search)
            """;

        const string dataSql = """
            SELECT
                p."Id", p."CategoryId", c."Name" AS "CategoryName",
                p."Name", p."Slug", p."Description", p."Brand",
                p."Price", p."Unit", p."Weight", p."ImageUrl",
                p."Sku", p."IsAvailable", p."IsOrganic", p."IsStoreBrand", p."Tags"
            FROM "Products" p
            JOIN "Categories" c ON p."CategoryId" = c."Id"
            WHERE p."IsAvailable" = true
            AND (LOWER(p."Name") LIKE @Search
                 OR LOWER(p."Description") LIKE @Search
                 OR LOWER(COALESCE(p."Brand", '')) LIKE @Search
                 OR LOWER(COALESCE(p."Tags", '')) LIKE @Search)
            ORDER BY
                CASE WHEN LOWER(p."Name") LIKE @Search THEN 0 ELSE 1 END,
                p."Name"
            LIMIT @Limit OFFSET @Offset
            """;

        var totalCount = await conn.ExecuteScalarAsync<int>(countSql, new { Search = searchTerm });
        var rows = await conn.QueryAsync<ProductSearchRow>(dataSql, new { Search = searchTerm, Limit = pageSize, Offset = offset });

        var items = rows.Select(r => new ProductDto(
            r.Id, r.CategoryId, r.CategoryName, r.Name, r.Slug,
            r.Description, r.Brand, r.Price, r.Unit, r.Weight,
            r.ImageUrl, r.Sku, r.IsAvailable, r.IsOrganic, r.IsStoreBrand, r.Tags,
            null // Active deal not joined in Dapper query for simplicity
        )).ToList();

        return new PagedResult<ProductDto>
        {
            Items = items,
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize
        };
    }

    private class ProductSearchRow
    {
        public Guid Id { get; set; }
        public Guid CategoryId { get; set; }
        public string CategoryName { get; set; } = "";
        public string Name { get; set; } = "";
        public string Slug { get; set; } = "";
        public string Description { get; set; } = "";
        public string? Brand { get; set; }
        public decimal Price { get; set; }
        public string Unit { get; set; } = "";
        public string? Weight { get; set; }
        public string? ImageUrl { get; set; }
        public string Sku { get; set; } = "";
        public bool IsAvailable { get; set; }
        public bool IsOrganic { get; set; }
        public bool IsStoreBrand { get; set; }
        public string? Tags { get; set; }
    }
}
