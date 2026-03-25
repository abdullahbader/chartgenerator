# New Features & Improvements

## Enhanced Customization Options

### 1. Individual Slice Colors
- **Before**: Only general color palette selection
- **Now**: Click on each pie slice's color circle to customize individual colors
- Colors are dynamically generated based on your selected column values
- Each slice can have its own unique color

### 2. Chart Dimensions
- **Width**: Adjustable from 400px to 2000px (default: 800px)
- **Height**: Adjustable from 300px to 1500px (default: 600px)
- Real-time preview updates as you adjust dimensions
- Dimensions are applied to PNG, PDF, and R code exports

### 3. Title Position Control
- **Horizontal Position**: 0 (Left) to 1 (Right), default 0.5 (Center)
- **Vertical Position**: 0 (Bottom) to 1 (Top), default 1.0 (Top)
- **Title Anchor**: Auto, Left, Center, or Right alignment
- Fine-tune where your chart title appears

### 4. Improved R Code Generation
- **Before**: Hardcoded static values in R code
- **Now**: Reads directly from your data source file (CSV/Excel)
- R code includes:
  - File reading instructions
  - Data preparation using dplyr
  - Proper handling of column names with spaces
  - All your customization settings (colors, fonts, dimensions, title position)
- Simply update the file path in the generated R code to match your file location

## How to Use New Features

### Individual Colors:
1. Select your chart type, dataset, and column
2. Generate the chart
3. Individual color pickers will appear for each slice
4. Click any color circle to change that specific slice's color
5. Regenerate the chart to see changes

### Chart Dimensions:
1. Use the width and height sliders in Step 4
2. Values update in real-time
3. Chart preview automatically adjusts

### Title Position:
1. Adjust horizontal and vertical sliders
2. Select title anchor alignment
3. Chart updates immediately

### R Code:
1. Generate your chart with all customizations
2. Click "Get R Code"
3. Copy the code
4. Update the file path in the R code to point to your data file
5. Run in R/RStudio

## Technical Details

- **Backend**: Enhanced to support all new customization parameters
- **Frontend**: Dynamic UI updates based on chart data
- **R Code**: Now generates production-ready code that reads from data sources
- **File Handling**: Uploaded datasets are saved to disk for R code reference

## Example R Code Output

```r
# Read data from CSV file
data <- read.csv("path/to/your/data.csv", stringsAsFactors = FALSE)

# Prepare data for pie chart
library(dplyr)
pie_data <- data %>%
    count(Category) %>%
    rename(category = Category, value = n)

# Create pie chart with your customizations
pie_chart <- ggplot(pie_data, aes(x = "", y = value, fill = category)) +
    geom_bar(stat = "identity", width = 1) +
    coord_polar("y", start = 0) +
    scale_fill_manual(values = c(
        "Electronics" = "#1f77b4",
        "Clothing" = "#ff7f0e",
        ...
    )) +
    labs(title = "Your Custom Title") +
    theme_void() +
    theme(...)

# Save chart
ggsave("pie_chart.png", pie_chart, width = 8, height = 6, dpi = 300)
```

Enjoy the enhanced customization capabilities! 🎨📊
