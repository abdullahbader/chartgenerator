import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/chart_type.dart';
import '../models/dataset.dart';
import 'chart_customization_screen.dart';

class ColumnSelectionScreen extends StatefulWidget {
  final ChartType chartType;
  final Dataset dataset;

  const ColumnSelectionScreen({
    super.key,
    required this.chartType,
    required this.dataset,
  });

  @override
  State<ColumnSelectionScreen> createState() => _ColumnSelectionScreenState();
}

class _ColumnSelectionScreenState extends State<ColumnSelectionScreen> {
  final ApiService _apiService = ApiService();
  List<String> _columns = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadColumns();
  }

  Future<void> _loadColumns() async {
    try {
      final columns = await _apiService.getDatasetColumns(widget.dataset.id);
      setState(() {
        _columns = columns;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading columns: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Select Column - ${widget.chartType.name}'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Dataset: ${widget.dataset.name}',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Select ${widget.chartType.maxColumns} column(s) for ${widget.chartType.name}',
                    style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                  ),
                  const SizedBox(height: 20),
                  Expanded(
                    child: _columns.isEmpty
                        ? const Center(
                            child: Text('No columns available'),
                          )
                        : ListView.builder(
                            itemCount: _columns.length,
                            itemBuilder: (context, index) {
                              final column = _columns[index];
                              return Card(
                                margin: const EdgeInsets.symmetric(vertical: 8),
                                child: ListTile(
                                  leading: const Icon(Icons.table_chart),
                                  title: Text(column),
                                  trailing: const Icon(Icons.arrow_forward_ios),
                                  onTap: () {
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (context) =>
                                            ChartCustomizationScreen(
                                          chartType: widget.chartType,
                                          dataset: widget.dataset,
                                          selectedColumn: column,
                                        ),
                                      ),
                                    );
                                  },
                                ),
                              );
                            },
                          ),
                  ),
                ],
              ),
            ),
    );
  }
}
