import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/chart_type.dart';
import '../models/dataset.dart';

class ApiService {
  final String baseUrl = 'http://localhost:5000/api';

  Future<List<ChartType>> getChartTypes() async {
    final response = await http.get(Uri.parse('$baseUrl/chart-types'));
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      final List<dynamic> chartTypesJson = data['chart_types'];
      return chartTypesJson.map((json) => ChartType.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load chart types');
    }
  }

  Future<List<Dataset>> getDatasets() async {
    final response = await http.get(Uri.parse('$baseUrl/datasets'));
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      final List<dynamic> datasetsJson = data['datasets'];
      return datasetsJson.map((json) => Dataset.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load datasets');
    }
  }

  Future<Map<String, dynamic>> uploadDataset(String filePath, String fileName) async {
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/datasets/upload'),
    );
    
    request.files.add(await http.MultipartFile.fromPath('file', filePath));
    
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to upload dataset');
    }
  }

  Future<List<String>> getDatasetColumns(String datasetId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/datasets/$datasetId/columns'),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return List<String>.from(data['columns']);
    } else {
      throw Exception('Failed to load dataset columns');
    }
  }

  Future<Map<String, dynamic>> generateChart({
    required String chartType,
    required String datasetId,
    required String column,
    required Map<String, dynamic> customization,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/charts/generate'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'chart_type': chartType,
        'dataset_id': datasetId,
        'column': column,
        'customization': customization,
      }),
    );
    
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      final error = json.decode(response.body);
      throw Exception(error['error'] ?? 'Failed to generate chart');
    }
  }

  Future<Map<String, dynamic>> exportChart({
    required String chartType,
    required String datasetId,
    required String column,
    required Map<String, dynamic> customization,
    required String format,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/charts/export'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'chart_type': chartType,
        'dataset_id': datasetId,
        'column': column,
        'customization': customization,
        'format': format,
      }),
    );
    
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      final error = json.decode(response.body);
      throw Exception(error['error'] ?? 'Failed to export chart');
    }
  }
}
