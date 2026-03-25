import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../services/api_service.dart';
import '../models/chart_type.dart';
import '../models/dataset.dart';
import 'column_selection_screen.dart';

class DatasetSelectionScreen extends StatefulWidget {
  final ChartType chartType;

  const DatasetSelectionScreen({
    super.key,
    required this.chartType,
  });

  @override
  State<DatasetSelectionScreen> createState() => _DatasetSelectionScreenState();
}

class _DatasetSelectionScreenState extends State<DatasetSelectionScreen> {
  final ApiService _apiService = ApiService();
  List<Dataset> _datasets = [];
  bool _isLoading = true;
  bool _isUploading = false;

  @override
  void initState() {
    super.initState();
    _loadDatasets();
  }

  Future<void> _loadDatasets() async {
    try {
      final datasets = await _apiService.getDatasets();
      setState(() {
        _datasets = datasets;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading datasets: $e')),
        );
      }
    }
  }

  Future<void> _uploadDataset() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['csv', 'xlsx', 'xls'],
      );

      if (result != null && result.files.single.path != null) {
        setState(() {
          _isUploading = true;
        });

        final uploadedDataset = await _apiService.uploadDataset(
          result.files.single.path!,
          result.files.single.name,
        );

        setState(() {
          _isUploading = false;
        });

        await _loadDatasets();

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Dataset uploaded successfully')),
          );
        }
      }
    } catch (e) {
      setState(() {
        _isUploading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error uploading dataset: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Select Dataset - ${widget.chartType.name}'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Available Datasets',
                        style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      ElevatedButton.icon(
                        onPressed: _isUploading ? null : _uploadDataset,
                        icon: _isUploading
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.upload),
                        label: const Text('Upload Dataset'),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: _datasets.isEmpty
                      ? Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.folder_open, size: 64, color: Colors.grey),
                              const SizedBox(height: 16),
                              const Text(
                                'No datasets available',
                                style: TextStyle(fontSize: 18, color: Colors.grey),
                              ),
                              const SizedBox(height: 8),
                              ElevatedButton.icon(
                                onPressed: _uploadDataset,
                                icon: const Icon(Icons.upload),
                                label: const Text('Upload Your First Dataset'),
                              ),
                            ],
                          ),
                        )
                      : ListView.builder(
                          itemCount: _datasets.length,
                          itemBuilder: (context, index) {
                            final dataset = _datasets[index];
                            return Card(
                              margin: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 8,
                              ),
                              child: ListTile(
                                leading: Icon(
                                  dataset.type == 'sample'
                                      ? Icons.description
                                      : Icons.cloud_upload,
                                  color: dataset.type == 'sample'
                                      ? Colors.blue
                                      : Colors.green,
                                ),
                                title: Text(dataset.name),
                                subtitle: Text(
                                  dataset.type == 'sample'
                                      ? 'Sample Dataset'
                                      : 'Uploaded Dataset',
                                ),
                                trailing: const Icon(Icons.arrow_forward_ios),
                                onTap: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (context) => ColumnSelectionScreen(
                                        chartType: widget.chartType,
                                        dataset: dataset,
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
    );
  }
}
