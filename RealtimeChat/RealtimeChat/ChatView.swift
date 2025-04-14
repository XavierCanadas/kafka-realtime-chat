//
//  ChatView.swift
//  RealtimeChat
//
//  Created by Xavi Cañadas on 14/4/25.
//

import SwiftUI

struct ChatView: View {
    let token: String
    
    var body: some View {
        VStack {
            Text("Welcome to Chat!")
                .font(.title)
                .padding()
            
            Text("Your session is active")
                .foregroundColor(.secondary)
            
            Text(token)
            
            // Here you would implement your actual chat interface
        }
        .navigationTitle("Realtime Chat")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("connect") {
                    // websocket connection
                }
            }
        }
    }
}

#Preview {
    NavigationStack {
        ChatView(token: "aa")
    }
    
}
