FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

COPY GroceryShop.sln ./
COPY src/GroceryShop.Core/GroceryShop.Core.csproj src/GroceryShop.Core/
COPY src/GroceryShop.Infrastructure/GroceryShop.Infrastructure.csproj src/GroceryShop.Infrastructure/
COPY src/GroceryShop.Api/GroceryShop.Api.csproj src/GroceryShop.Api/
COPY src/GroceryShop.Functions/GroceryShop.Functions.csproj src/GroceryShop.Functions/
RUN dotnet restore

COPY src/ src/
RUN dotnet publish src/GroceryShop.Api/GroceryShop.Api.csproj -c Release -o /app

FROM mcr.microsoft.com/dotnet/aspnet:8.0
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN groupadd -r grocery && useradd -r -g grocery -s /sbin/nologin grocery
WORKDIR /app
COPY --from=build /app .
RUN chown -R grocery:grocery /app
USER grocery
ENV ASPNETCORE_URLS=http://+:8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -sf http://localhost:8000/health || exit 1
ENTRYPOINT ["dotnet", "GroceryShop.Api.dll"]
