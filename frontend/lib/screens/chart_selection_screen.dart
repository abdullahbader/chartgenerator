import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/chart_type.dart';
import 'dataset_selection_screen.dart';

class ChartSelectionScreen extends StatefulWidget {
  const ChartSelectionScreen({super.key});

  @override
  State<ChartSelectionScreen> createState() => _ChartSelectionScreenState();
}

class _ChartSelectionScreenState extends State<ChartSelectionScreen> {
  final ApiService _apiService = ApiService();
  List<ChartType> _chartTypes = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadChartTypes();
  }

  Future<void> _loadChartTypes() async {
    try {
      final chartTypes = await _apiService.getChartTypes();
      setState(() {
        _chartTypes = chartTypes;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading chart types: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Charts Generator'),
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Select Chart Type',
                    style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 20),
                  Expanded(
                    child: GridView.builder(
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        crossAxisSpacing: 16,
                        mainAxisSpacing: 16,
                        childAspectRatio: 1.2,
                      ),
                      itemCount: _chartTypes.length,
                      itemBuilder: (context, index) {
                        final chartType = _chartTypes[index];
                        return _buildChartTypeCard(chartType);
                      },
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildChartTypeCard(ChartType chartType) {
    IconData icon;
    Color color;

    switch (chartType.id) {
      case 'pie':
        icon = Icons.pie_chart;
        color = Colors.blue;
        break;
      default:
        icon = Icons.bar_chart;
        color = Colors.grey;
    }

    return Card(
      elevation: 4,
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => DatasetSelectionScreen(
                chartType: chartType,
              ),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 48, color: color),
              const SizedBox(height: 12),
              Text(
                chartType.name,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                chartType.description,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
