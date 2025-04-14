//
//  ContentView.swift
//  RealtimeChat
//
//  Created by Xavi Cañadas on 21/3/25.
//

import SwiftUI

struct ContentView: View {
    @State private var username: String = ""
    @State private var password: String = ""
    @State private var token: String?
    @State private var isLoading = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var isLoggedIn = false

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Username", text: $username)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)
                    SecureField("Password", text: $password)
                }
                
                Section {
                    Button {
                        Task {
                            await login()
                        }
                    } label: {
                        HStack {
                            Spacer()
                            if isLoading {
                                ProgressView()
                                    .tint(.white)
                            } else {
                                Text("Login")
                                    .fontWeight(.semibold)
                            }
                            Spacer()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                    .disabled(username.isEmpty || password.isEmpty || isLoading)
                }
                .listRowBackground(Color.clear)
            }
            .navigationTitle("Log in")
            .alert("Login Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
            .navigationDestination(isPresented: $isLoggedIn) {
                ChatView(token: token ?? "")
            }
        }
    }
    
    func login() async {
            isLoading = true
            defer { isLoading = false }
            
            // configure the request
            guard let url = URL(string: "http://localhost:5002/token") else {
                showErrorMessage("Invalid server URL")
                return
            }
            
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
            
            let bodyParams = "username=\(username.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")&password=\(password.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")"
            
            request.httpBody = bodyParams.data(using: .utf8)
            
            // send the request
            do {
                let (data, response) = try await URLSession.shared.data(for: request)
                
                // Check HTTP response status code
                guard let httpResponse = response as? HTTPURLResponse else {
                    showErrorMessage("Invalid response from server")
                    return
                }
                
                if !(200...299).contains(httpResponse.statusCode) {
                    showErrorMessage("Server error: \(httpResponse.statusCode)")
                    return
                }
                
                // Parse the response data
                if let responseJSON = try? JSONDecoder().decode([String: String].self, from: data),
                   let receivedToken = responseJSON["access_token"] {
                    
                    
                    self.token = receivedToken
                    print("Login successful! Token: \(receivedToken)")
                    isLoggedIn = true
                    
                } else {
                    showErrorMessage("Failed to parse token from response")
                }
            } catch {
                // Handle network errors
                showErrorMessage("Network error: \(error.localizedDescription)")
            }
        }
    private func showErrorMessage(_ message: String) {
        
        errorMessage = message
        showError = true
        
    }
}



#Preview {
    
    ContentView()
    
}

