import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import '../services/api_service.dart';
import '../models/chart_type.dart';
import '../models/dataset.dart';

class ChartPreviewScreen extends StatefulWidget {
  final ChartType chartType;
  final Dataset dataset;
  final String selectedColumn;
  final Map<String, dynamic> customization;
  final Map<String, dynamic> chartData;

  const ChartPreviewScreen({
    super.key,
    required this.chartType,
    required this.dataset,
    required this.selectedColumn,
    required this.customization,
    required this.chartData,
  });

  @override
  State<ChartPreviewScreen> createState() => _ChartPreviewScreenState();
}

class _ChartPreviewScreenState extends State<ChartPreviewScreen> {
  final ApiService _apiService = ApiService();
  bool _isExporting = false;
  String? _exportMessage;

  Future<void> _exportChart(String format) async {
    setState(() {
      _isExporting = true;
      _exportMessage = null;
    });

    try {
      final exportData = await _apiService.exportChart(
        chartType: widget.chartType.id,
        datasetId: widget.dataset.id,
        column: widget.selectedColumn,
        customization: widget.customization,
        format: format,
      );

      if (format == 'r') {
        // Show R code in a dialog
        _showRCodeDialog(exportData['code']);
      } else {
        // Save file
        await _saveFile(format, exportData);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error exporting chart: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isExporting = false;
        });
      }
    }
  }

  Future<void> _saveFile(String format, Map<String, dynamic> exportData) async {
    try {
      final directory = await getApplicationDocumentsDirectory();
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final filename = 'chart_$timestamp.$format';
      final file = File('${directory.path}/$filename');

      if (format == 'png' || format == 'pdf') {
        // Decode base64 and save
        final bytes = base64Decode(exportData['data']);
        await file.writeAsBytes(bytes);
      } else if (format == 'html') {
        // Save HTML content
        await file.writeAsString(exportData['content']);
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Chart exported to: ${file.path}'),
            action: SnackBarAction(
              label: 'Share',
              onPressed: () => Share.shareXFiles([XFile(file.path)]),
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error saving file: $e')),
        );
      }
    }
  }

  void _showRCodeDialog(String rCode) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('R Code'),
        content: SizedBox(
          width: double.maxFinite,
          child: SingleChildScrollView(
            child: SelectableText(
              rCode,
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Clipboard.setData(ClipboardData(text: rCode));
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('R code copied to clipboard')),
              );
            },
            child: const Text('Copy'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Chart Preview'),
        actions: [
          PopupMenuButton<String>(
            onSelected: _exportChart,
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'png',
                child: Row(
                  children: [
                    Icon(Icons.image, size: 20),
                    SizedBox(width: 8),
                    Text('Export as PNG'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'pdf',
                child: Row(
                  children: [
                    Icon(Icons.picture_as_pdf, size: 20),
                    SizedBox(width: 8),
                    Text('Export as PDF'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'html',
                child: Row(
                  children: [
                    Icon(Icons.code, size: 20),
                    SizedBox(width: 8),
                    Text('Export as HTML'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'r',
                child: Row(
                  children: [
                    Icon(Icons.integration_instructions, size: 20),
                    SizedBox(width: 8),
                    Text('Get R Code'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          // Chart Preview Placeholder
          Expanded(
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.pie_chart, size: 120, color: Colors.blue),
                  const SizedBox(height: 16),
                  Text(
                    widget.customization['title'] ?? 'Chart Preview',
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Chart data generated successfully',
                    style: TextStyle(color: Colors.grey[600]),
                  ),
                  const SizedBox(height: 32),
                  if (_isExporting)
                    const CircularProgressIndicator()
                  else
                    Wrap(
                      spacing: 16,
                      runSpacing: 16,
                      alignment: WrapAlignment.center,
                      children: [
                        ElevatedButton.icon(
                          onPressed: () => _exportChart('png'),
                          icon: const Icon(Icons.image),
                          label: const Text('PNG'),
                        ),
                        ElevatedButton.icon(
                          onPressed: () => _exportChart('pdf'),
                          icon: const Icon(Icons.picture_as_pdf),
                          label: const Text('PDF'),
                        ),
                        ElevatedButton.icon(
                          onPressed: () => _exportChart('html'),
                          icon: const Icon(Icons.code),
                          label: const Text('HTML'),
                        ),
                        ElevatedButton.icon(
                          onPressed: () => _exportChart('r'),
                          icon: const Icon(Icons.integration_instructions),
                          label: const Text('R Code'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green,
                            foregroundColor: Colors.white,
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ),
          ),
          // Chart Info
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.grey[100],
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Chart Information',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.grey[800],
                  ),
                ),
                const SizedBox(height: 8),
                _buildInfoRow('Type', widget.chartType.name),
                _buildInfoRow('Dataset', widget.dataset.name),
                _buildInfoRow('Column', widget.selectedColumn),
                _buildInfoRow('Font', '${widget.customization['font_family']} (${widget.customization['font_size']}pt)'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              '$label:',
              style: TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(color: Colors.grey[800]),
            ),
          ),
        ],
      ),
    );
  }
}
