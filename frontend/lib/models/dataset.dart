class Dataset {
  final String id;
  final String name;
  final String type;

  Dataset({
    required this.id,
    required this.name,
    required this.type,
  });

  factory Dataset.fromJson(Map<String, dynamic> json) {
    return Dataset(
      id: json['id'],
      name: json['name'],
      type: json['type'],
    );
  }
}
