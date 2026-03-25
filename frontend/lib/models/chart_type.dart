class ChartType {
  final String id;
  final String name;
  final String description;
  final int maxColumns;

  ChartType({
    required this.id,
    required this.name,
    required this.description,
    required this.maxColumns,
  });

  factory ChartType.fromJson(Map<String, dynamic> json) {
    return ChartType(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      maxColumns: json['max_columns'],
    );
  }
}
