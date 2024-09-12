import { toast } from "@/components/ui/use-toast";

const authFetcher = async (
  url: string,
  accessToken?: string,
  method?: string,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  body?: any,
) => {
  /*
    Fetch data from the server with the access token
    */

  {
    if (!accessToken) {
      return;
    }
    if (!method) {
      method = "GET";
    }
    if (!body) {
      body = null;
    } else {
      body = JSON.stringify(body);
    }
    // Headers
    const headers = {
      Authorization: "Bearer " + accessToken,
      "Content-Type": "application/json",
    };
    const response = await fetch(url, { method, headers: headers, body });
    if (response.ok) {
      const response_json = await response.json();
      return response_json;
    } else {
      console.error("Error fetching data:", response);
      toast({
        title: "Error fetching data",
        description: response.statusText,
      });
      return undefined;
    }
  }
};

const nonAuthFetcher = async (url: string, method?: string) => {
  const response = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
  });
  if (response.ok) {
    return await response.json();
  } else {
    console.error("Error fetching data:", response);
    toast({
      title: "Error fetching data",
      description: response.statusText,
    });
    return undefined;
  }
};

export { authFetcher, nonAuthFetcher };
