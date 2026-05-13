import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/estacion.dart';
import 'auth_service.dart';

class ApiService {
    late final String baseUrl;
    
    ApiService() {
        if (kIsWeb) {
            baseUrl = "http://localhost:8000";
        } else {
            baseUrl = "http://10.0.2.2:8000";
        }
    }

    Future<List<Estacion>> fetchEstaciones() async {
        try {
            final response = await http
                .get(Uri.parse('$baseUrl/estaciones/'))
                .timeout(const Duration(seconds: 5)); // ← Timeout 5 segundos

            if (response.statusCode == 200) {
                List jsonResponse = json.decode(response.body);
                return jsonResponse.map((data) => Estacion.fromJson(data)).toList();
            } else {
                throw Exception('Error del servidor: ${response.statusCode}');
            }
        } catch (e) {
            // Esto evita que la App se cierre inesperadamente
            throw Exception('No se pudo conectar con SMAT. ¿Está el servidor activo?');
        }
    }

    Future<bool> crearEstacion(String nombre, String ubicacion) async {
        try {
            final token = await AuthService().getToken();
            final response = await http
                .post(
                    Uri.parse('$baseUrl/estaciones/'),
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer $token',
                    },
                    body: jsonEncode({'nombre': nombre, 'ubicacion': ubicacion}),
                )
                .timeout(const Duration(seconds: 5));
            return response.statusCode == 200 || response.statusCode == 201;
        } catch (e) {
            throw Exception('No se pudo conectar con el servidor');
        }
    }

    Future<bool> eliminarEstacion(int id) async {
        try {
            final token = await AuthService().getToken();
            final response = await http
                .delete(
                    Uri.parse('$baseUrl/estaciones/$id'),
                    headers: {'Authorization': 'Bearer $token'},
                )
                .timeout(const Duration(seconds: 5));
            return response.statusCode == 200;
        } catch (e) {
            throw Exception('Error al eliminar');
        }
    }

    Future<bool> editarEstacion(int id, String nombre, String ubicacion) async {
        try {
            final token = await AuthService().getToken();
            final response = await http
                .put(
                    Uri.parse('$baseUrl/estaciones/$id'),
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer $token',
                    },
                    body: jsonEncode({'nombre': nombre, 'ubicacion': ubicacion}),
                )
                .timeout(const Duration(seconds: 5));
            return response.statusCode == 200;
        } catch (e) {
            throw Exception('Error al editar');
        }
    }

    Future<double?> getUltimaLectura(int estacionId) async {
        try {
            final token = await AuthService().getToken();
            final response = await http
                .get(
                    Uri.parse('$baseUrl/estaciones/$estacionId/lecturas'),
                    headers: {'Authorization': 'Bearer $token'},
                )
                .timeout(const Duration(seconds: 5));
            if (response.statusCode == 200) {
                List data = json.decode(response.body);
                if (data.isNotEmpty) {
                    return data.last['valor']?.toDouble();
                }
            }
            return null;
        } catch (e) {
            return null;
        }
    }
}