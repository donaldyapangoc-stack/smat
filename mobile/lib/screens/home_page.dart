import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../models/estacion.dart';
import 'login_screen.dart';
import 'add_estacion.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  late Future<List<Estacion>> futureEstaciones;
  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _cargarEstaciones();
  }

  void _cargarEstaciones() {
    futureEstaciones = _apiService.fetchEstaciones();
  }

  void _refreshData() {
    setState(() {
      _cargarEstaciones();
    });
  }

  // Obtener color del icono según la última lectura
  Future<Color> _getIconColor(int estacionId) async {
    double? ultimaLectura = await _apiService.getUltimaLectura(estacionId);
    if (ultimaLectura == null) return Colors.grey;
    if (ultimaLectura > 20) return Colors.red;
    if (ultimaLectura > 10) return Colors.orange;
    return Colors.green;
  }

  // Diálogo para editar estación
  void _mostrarDialogoEdicion(Estacion estacion) {
    final nombreCtrl = TextEditingController(text: estacion.nombre);
    final ubicacionCtrl = TextEditingController(text: estacion.ubicacion);
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Editar Estación"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nombreCtrl,
              decoration: const InputDecoration(labelText: "Nombre"),
            ),
            TextField(
              controller: ubicacionCtrl,
              decoration: const InputDecoration(labelText: "Ubicación"),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancelar"),
          ),
          ElevatedButton(
            onPressed: () async {
              bool ok = await _apiService.editarEstacion(
                estacion.id,
                nombreCtrl.text,
                ubicacionCtrl.text,
              );
              if (ok) {
                Navigator.pop(context);
                _refreshData();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Estación actualizada')),
                );
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Error al actualizar')),
                );
              }
            },
            child: const Text("Guardar"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Estaciones SMAT'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await AuthService().logout();
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (context) => const LoginScreen()),
                (route) => false,
              );
            },
          )
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          _refreshData();
          await Future.delayed(const Duration(seconds: 1));
        },
        child: FutureBuilder<List<Estacion>>(
          future: futureEstaciones,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            } else if (snapshot.hasError) {
              return Center(
                child: Text('❌ Error de conexion: ${snapshot.error}'),
              );
            } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
              return const Center(
                child: Text('No hay estaciones'),
              );
            } else {
              return ListView.builder(
                itemCount: snapshot.data!.length,
                itemBuilder: (context, index) {
                  final estacion = snapshot.data![index];
                  
                  return Dismissible(
                    key: Key(estacion.id.toString()),
                    direction: DismissDirection.endToStart,
                    background: Container(
                      color: Colors.red,
                      alignment: Alignment.centerRight,
                      padding: const EdgeInsets.only(right: 20),
                      child: const Icon(Icons.delete, color: Colors.white),
                    ),
                    onDismissed: (direction) async {
                      bool ok = await _apiService.eliminarEstacion(estacion.id);
                      if (ok) {
                        _refreshData();
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('${estacion.nombre} eliminada')),
                        );
                      } else {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Error al eliminar')),
                        );
                      }
                    },
                    child: ListTile(
                      leading: FutureBuilder<Color>(
                        future: _getIconColor(estacion.id),
                        builder: (context, snapshot) {
                          return Icon(
                            Icons.satellite_alt,
                            color: snapshot.data ?? Colors.grey,
                          );
                        },
                      ),
                      title: Text(estacion.nombre),
                      subtitle: Text(estacion.ubicacion),
                      onTap: () => _mostrarDialogoEdicion(estacion),
                    ),
                  );
                },
              );
            }
          },
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => AddEstacionScreen()),
          );
          if (result == true) {
            _refreshData();
          }
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}